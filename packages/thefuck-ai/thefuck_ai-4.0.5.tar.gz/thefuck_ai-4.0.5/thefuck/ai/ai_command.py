# -*- coding: utf-8 -*-
"""AI Command entry point for TheFuck-AI.

Provides the main entry point for AI-powered command generation.
"""
from ..conf import settings
from .context import ContextCollector
from .ai_provider import AIProvider
from .security import SecurityChecker, RiskLevel
from .exceptions import AIError, AIConfigError


class AICommand:
    """Main AI command handler."""

    def __init__(self):
        """Initialize AI command handler."""
        self._context_collector = ContextCollector()
        self._security_checker = SecurityChecker()
        self._provider = None  # Lazy initialization

    def _get_provider(self):
        """Get or create AI provider (lazy init).

        Returns:
            AIProvider: The AI provider instance.
        """
        if self._provider is None:
            self._provider = AIProvider()
        return self._provider

    def process(self, user_input, failed_command=None, error_output=None):
        """Process user input and generate AI command.

        Args:
            user_input: User's description of what they want.
            failed_command: Optional failed command that triggered this.
            error_output: Optional error output from failed command.

        Returns:
            dict: Result containing command, risk level, and metadata.
        """
        result = {
            'command': None,
            'risk_level': None,
            'requires_confirmation': False,
            'blocked': False,
            'error': None,
            'reasons': [],
        }

        try:
            # Collect context
            context = self._context_collector.collect()

            # Generate command from AI
            provider = self._get_provider()
            command = provider.generate_command(
                user_input,
                context=context,
                failed_command=failed_command,
                error_output=error_output
            )

            if not command:
                result['error'] = "AI was unable to suggest a command"
                return result

            # Check security
            risk_level = self._security_checker.check(command)
            reasons = self._security_checker.get_risk_reasons(command)

            result['command'] = command
            result['risk_level'] = risk_level
            result['reasons'] = reasons
            result['requires_confirmation'] = \
                self._security_checker.requires_confirmation(command)

            # Block high risk commands
            if risk_level == RiskLevel.HIGH:
                result['blocked'] = True
                result['error'] = "Command blocked due to high security risk"

            return result

        except AIConfigError as e:
            result['error'] = str(e)
            return result
        except AIError as e:
            result['error'] = "AI error: {}".format(str(e))
            return result
        except Exception as e:
            result['error'] = "Unexpected error: {}".format(str(e))
            return result

    def is_ai_trigger(self, command):
        """Check if command is an AI trigger.

        Args:
            command: The command to check.

        Returns:
            tuple: (is_trigger, user_request) or (False, None)
        """
        trigger_word = settings.ai_trigger_word or 'ai'

        if not command:
            return False, None

        # Check for trigger word at start
        parts = command.split(None, 1)
        if not parts:
            return False, None

        if parts[0].lower() == trigger_word:
            user_request = parts[1] if len(parts) > 1 else ''
            return True, user_request

        return False, None


def process_ai_command(user_input, failed_command=None, error_output=None):
    """Convenience function to process AI command.

    Args:
        user_input: What the user wants.
        failed_command: Failed command if any.
        error_output: Error output if any.

    Returns:
        dict: Processing result.
    """
    handler = AICommand()
    return handler.process(user_input, failed_command, error_output)


def is_ai_trigger(command):
    """Check if command is AI trigger.

    Args:
        command: Command to check.

    Returns:
        tuple: (is_trigger, user_request)
    """
    handler = AICommand()
    return handler.is_ai_trigger(command)
