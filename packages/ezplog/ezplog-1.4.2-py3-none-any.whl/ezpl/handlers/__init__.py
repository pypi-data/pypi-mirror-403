# ///////////////////////////////////////////////////////////////
# EZPL - Handlers Module
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Handlers module for Ezpl logging framework.

This module contains concrete implementations of logging handlers.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .console import ConsolePrinter, ConsolePrinterWrapper
from .file import FileLogger
from .wizard import RichWizard

# Public API aliases
# EzPrinter is the actual printer class (ConsolePrinter)
# ConsolePrinterWrapper is returned by ConsolePrinter.get_printer()
EzPrinter = ConsolePrinter
EzLogger = FileLogger

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Handler class exports
    "ConsolePrinter",
    "ConsolePrinterWrapper",
    "FileLogger",
    "RichWizard",
    # Public API exports
    "EzPrinter",
    "EzLogger",
]
