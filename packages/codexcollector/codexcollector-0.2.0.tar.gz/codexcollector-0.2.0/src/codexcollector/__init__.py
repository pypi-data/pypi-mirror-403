"""
CodexCollector - Document collection and text extraction across multiple formats.

A unified interface for ingesting documents from filesystems and web URLs,
with support for Word, PowerPoint, PDF, and plain text formats.
"""

from codexcollector.codexcollector import CodexCollector, Document
from codexcollector.codex_exceptions import IngestionError, ConfigurationError

__version__ = "0.2.0"
__author__ = "NotAndroid37"
__license__ = "MIT"

__all__ = [
    "CodexCollector",
    "Document",
    "IngestionError",
    "ConfigurationError",
    "__version__",
]
