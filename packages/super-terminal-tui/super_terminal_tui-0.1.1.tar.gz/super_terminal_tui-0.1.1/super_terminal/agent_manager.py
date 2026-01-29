import os
import pty
import select
import shlex
import subprocess
import threading
import fcntl
import termios
import struct
import pyte
import codecs
from queue import Queue

class AgentProcess:
    def __init__(self, name, command, cwd):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.output_queue = Queue()
        self.history = []
        self.process = None
        self.master_fd = None
        self.is_running = False
        self.screen = None
        self.stream = None
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def start(self, cols=80, rows=24):
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.Stream(self.screen)
        
        self.master_fd, slave_fd = pty.openpty()
        self._set_pty_size(self.master_fd, cols, rows)
        
        self.process = subprocess.Popen(
            shlex.split(self.command),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self.cwd,
            preexec_fn=os.setsid,
            close_fds=True,
            env={**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor"}
        )
        os.close(slave_fd)
        self.is_running = True
        threading.Thread(target=self._read_output, daemon=True).start()

    def _set_pty_size(self, fd, cols, rows):
        buf = struct.pack('HHHH', int(rows), int(cols), 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, buf)

    def resize(self, cols, rows):
        if self.master_fd is not None:
            self._set_pty_size(self.master_fd, cols, rows)
        if self.screen:
            self.screen.resize(int(rows), int(cols))

    def _read_output(self):
        while self.is_running and self.master_fd is not None:
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    raw_data = os.read(self.master_fd, 4096)
                    if raw_data:
                        data = self._decoder.decode(raw_data)
                        self.output_queue.put(data)
                        if self.stream:
                            self.stream.feed(data)
                    else:
                        self.is_running = False
            except (EOFError, OSError, ValueError):
                self.is_running = False
                break
        
        if self.process:
            self.process.wait()
        self.is_running = False

    def get_screen_text(self):
        if not self.screen:
            return ""
        return "\n".join(self.screen.display)

    def send_input(self, text):
        if self.is_running and self.master_fd:
            os.write(self.master_fd, text.encode('utf-8'))

    def stop(self):
        self.is_running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass

class AgentManager:
    def __init__(self):
        self.agents = {}

    def add_agent(self, name, command, cwd):
        agent = AgentProcess(name, command, cwd)
        self.agents[name] = agent
        return agent

    def get_agent(self, name):
        return self.agents.get(name)

    def remove_agent(self, name):
        agent = self.agents.pop(name, None)
        if agent:
            agent.stop()

    def stop_all(self):
        for agent in self.agents.values():
            agent.stop()
