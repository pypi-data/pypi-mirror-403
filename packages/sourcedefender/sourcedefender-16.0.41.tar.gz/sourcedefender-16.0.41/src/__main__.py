"""
SOURCEdefender CLI Entry Point
==============================

This module provides the command-line interface entry point for SOURCEdefender.
It is invoked when running:
    - `sourcedefender <command>` (console script)
    - `python -m sourcedefender <command>` (module execution)

The CLI delegates to the engine module which handles:
    - encrypt: Encrypt .py files to .pye format
    - activate: Activate license with token
    - validate: Check license status
    - pack: Bundle encrypted files with PyInstaller
    - changelog: Display version history

Example:
    $ sourcedefender encrypt --remove myfile.py
    $ python -m sourcedefender validate
"""
from . import engine
