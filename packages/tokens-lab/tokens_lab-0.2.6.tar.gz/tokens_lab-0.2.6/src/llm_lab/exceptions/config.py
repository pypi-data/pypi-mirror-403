"""Configuration-specific exception classes."""

from typing import Optional
from .base import ConfigurationError


class MissingConfigError(ConfigurationError):
    """Raised when a required environment variable is missing."""
    
    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        suggestion = f"Add {variable_name} to your .env file"
        self.suggestion = suggestion
        
        full_message = f"Missing required environment variable: {variable_name}"
        full_message += f"\nSuggestion: {suggestion}"
        
        super().__init__(full_message)


class InvalidConfigError(ConfigurationError):
    """Raised when an environment variable has an invalid value."""
    
    def __init__(self, variable_name: str, expected_type: str, actual_value: str):
        self.variable_name = variable_name
        suggestion = f"Check your .env file and ensure {variable_name} is a valid {expected_type}"
        self.suggestion = suggestion
        
        full_message = f"Invalid value for {variable_name}: expected {expected_type}, got '{actual_value}'"
        full_message += f"\nSuggestion: {suggestion}"
        
        super().__init__(full_message)
