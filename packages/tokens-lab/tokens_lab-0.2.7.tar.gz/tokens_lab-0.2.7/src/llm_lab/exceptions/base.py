"""Base exception classes for LLM Lab library."""

class llmLabError(Exception):
    """Base exception for all LLM Lab library errors."""


class ConfigurationError(llmLabError):
    """Raised for invalid or missing configuration values."""


class EnvironmentError(llmLabError):
    """Raised when required runtime environment or dependencies are not available."""


class FileTextIOError(llmLabError):
    """Base exception for `llm_lab.filetextio` domain."""


class UnsupportedFileTypeError(FileTextIOError):
    """Raised when a file extension is not supported by the parser registry."""


class ParseError(FileTextIOError):
    """Raised when a parser fails to extract text from a file."""
