"""
Sharer - Effortless Screen Sharing
Cast your screen to any device via browser - no installation required
"""

__version__ = "1.0.0"

from .server import start_server

__all__ = ['start_server']