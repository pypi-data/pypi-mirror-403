"""
Main entry point for Super Terminal package.
"""

from .app import SuperTerminal

def main():
    """Run the Super Terminal application."""
    app = SuperTerminal()
    app.run()

if __name__ == "__main__":
    main()
