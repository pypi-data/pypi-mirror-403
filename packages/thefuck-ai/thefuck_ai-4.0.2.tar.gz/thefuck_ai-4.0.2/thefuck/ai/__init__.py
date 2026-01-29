# -*- coding: utf-8 -*-
"""TheFuck-AI Module

AI-powered command generation for TheFuck.
"""

__version__ = '0.1.0'

from .ai_command import AICommand, process_ai_command, is_ai_trigger
from .ai_provider import AIProvider, generate_ai_command
from .context import ContextCollector, collect_context
from .security import SecurityChecker, RiskLevel, check_command_safety
from .exceptions import (
    AIError, AIConfigError, AIAPIError, AITimeoutError,
    AIRateLimitError, AIAuthenticationError, SecurityError,
    HighRiskCommandError, SensitiveDataError, ContextError, ParseError
)

__all__ = [
    # Version
    '__version__',
    # Main entry
    'AICommand', 'process_ai_command', 'is_ai_trigger',
    # AI Provider
    'AIProvider', 'generate_ai_command',
    # Context
    'ContextCollector', 'collect_context',
    # Security
    'SecurityChecker', 'RiskLevel', 'check_command_safety',
    # Exceptions
    'AIError', 'AIConfigError', 'AIAPIError', 'AITimeoutError',
    'AIRateLimitError', 'AIAuthenticationError', 'SecurityError',
    'HighRiskCommandError', 'SensitiveDataError', 'ContextError', 'ParseError',
]
