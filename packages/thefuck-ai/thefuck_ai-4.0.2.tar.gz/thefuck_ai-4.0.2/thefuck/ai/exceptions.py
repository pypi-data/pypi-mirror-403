# -*- coding: utf-8 -*-
"""Custom exceptions for TheFuck-AI module."""


class AIError(Exception):
    """Base exception for all AI-related errors."""
    pass


class AIConfigError(AIError):
    """Configuration-related errors."""
    pass


class AIAPIError(AIError):
    """API call related errors."""

    def __init__(self, message, status_code=None, response=None):
        super(AIAPIError, self).__init__(message)
        self.status_code = status_code
        self.response = response


class AITimeoutError(AIAPIError):
    """API request timeout."""
    pass


class AIRateLimitError(AIAPIError):
    """API rate limit exceeded."""
    pass


class AIAuthenticationError(AIAPIError):
    """API authentication failed."""
    pass


class SecurityError(AIError):
    """Security-related errors."""
    pass


class HighRiskCommandError(SecurityError):
    """Command identified as high risk."""

    def __init__(self, command, risk_level, reasons=None):
        message = "High risk command blocked: {}".format(command)
        super(HighRiskCommandError, self).__init__(message)
        self.command = command
        self.risk_level = risk_level
        self.reasons = reasons or []


class SensitiveDataError(SecurityError):
    """Sensitive data detected in command or output."""

    def __init__(self, message, pattern=None):
        super(SensitiveDataError, self).__init__(message)
        self.pattern = pattern


class ContextError(AIError):
    """Context collection errors."""
    pass


class ParseError(AIError):
    """Response parsing errors."""
    pass
