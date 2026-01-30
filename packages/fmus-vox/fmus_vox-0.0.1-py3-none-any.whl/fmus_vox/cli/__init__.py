"""
fmus_vox.cli - Command-line interface for fmus-vox

This module provides a comprehensive CLI for interacting with fmus-vox
functionality from the command line.
"""

from fmus_vox.cli.commands import app, transcribe_cmd, speak_cmd, interact_cmd, clone_cmd, serve_cmd

__all__ = ["app", "transcribe_cmd", "speak_cmd", "interact_cmd", "clone_cmd", "serve_cmd", "main"]


def main():
    """Main entry point for the CLI."""
    app()
