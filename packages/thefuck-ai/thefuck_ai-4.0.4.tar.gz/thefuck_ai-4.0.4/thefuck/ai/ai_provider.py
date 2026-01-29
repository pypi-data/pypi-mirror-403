# -*- coding: utf-8 -*-
"""AI Provider module for TheFuck-AI.

Handles communication with AI APIs (DeepSeek) for command generation.
"""
import json
import re
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

from ..conf import settings
from .exceptions import (
    AIConfigError, AIAPIError, AITimeoutError,
    AIRateLimitError, AIAuthenticationError, ParseError
)


class AIProvider:
    """AI service provider for command generation."""

    SYSTEM_PROMPT = """You are an expert shell command assistant. Your task is to suggest the correct command based on user input and context.

Rules:
1. Return ONLY the corrected command, nothing else
2. Do not include explanations or markdown formatting
3. Consider the user's shell, OS, and working directory
4. Use the command history for context
5. Be conservative - prefer safe operations

If you cannot determine a safe command, return: UNABLE_TO_SUGGEST"""

    def __init__(self, api_key=None, endpoint=None, model=None, timeout=None):
        """Initialize AI provider.

        Args:
            api_key: API key for authentication.
            endpoint: API endpoint URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or settings.ai_api_key
        self.endpoint = endpoint or settings.ai_endpoint
        self.model = model or settings.ai_model
        self.timeout = timeout or settings.ai_timeout

        if not self.api_key:
            raise AIConfigError("AI API key not configured. "
                                "Set THEFUCK_AI_API_KEY environment variable.")

    def generate_command(self, user_request, context=None, failed_command=None,
                         error_output=None):
        """Generate a command suggestion from AI.

        Args:
            user_request: User's description of what they want.
            context: Execution context dictionary.
            failed_command: The command that failed (optional).
            error_output: Error output from failed command (optional).

        Returns:
            str: Suggested command or None if unable to suggest.
        """
        prompt = self._build_prompt(user_request, context, failed_command,
                                    error_output)
        response = self._call_api(prompt)
        return self._parse_response(response)

    def _build_prompt(self, user_request, context=None, failed_command=None,
                      error_output=None):
        """Build the prompt for the AI.

        Args:
            user_request: User's description.
            context: Execution context.
            failed_command: Failed command if any.
            error_output: Error output if any.

        Returns:
            str: Constructed prompt.
        """
        parts = []

        if failed_command:
            parts.append("Failed command: {}".format(failed_command))
        if error_output:
            # Truncate long output
            max_len = settings.ai_max_output_length or 1000
            if len(error_output) > max_len:
                error_output = error_output[:max_len] + "... [truncated]"
            parts.append("Error output: {}".format(error_output))

        parts.append("User request: {}".format(user_request))

        if context:
            if context.get('cwd'):
                parts.append("Working directory: {}".format(context['cwd']))
            if context.get('system'):
                sys_info = context['system']
                parts.append("System: {} {} ({})".format(
                    sys_info.get('os', 'unknown'),
                    sys_info.get('shell', 'unknown'),
                    sys_info.get('architecture', 'unknown')
                ))
            if context.get('history'):
                history_str = '\n'.join(context['history'][-5:])
                parts.append("Recent commands:\n{}".format(history_str))

        return '\n\n'.join(parts)

    def _call_api(self, prompt):
        """Call the AI API.

        Args:
            prompt: The prompt to send.

        Returns:
            dict: API response.

        Raises:
            AIAPIError: On API errors.
            AITimeoutError: On timeout.
            AIAuthenticationError: On auth failure.
            AIRateLimitError: On rate limit.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_key),
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self.SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.3,
            'max_tokens': 256,
        }

        data = json.dumps(payload).encode('utf-8')
        request = Request(self.endpoint, data=data, headers=headers)

        try:
            response = urlopen(request, timeout=self.timeout)
            return json.loads(response.read().decode('utf-8'))
        except HTTPError as e:
            status_code = e.code
            try:
                error_body = json.loads(e.read().decode('utf-8'))
            except (ValueError, AttributeError):
                error_body = None

            if status_code == 401:
                raise AIAuthenticationError(
                    "Authentication failed. Check your API key.",
                    status_code=status_code,
                    response=error_body
                )
            elif status_code == 429:
                raise AIRateLimitError(
                    "Rate limit exceeded. Try again later.",
                    status_code=status_code,
                    response=error_body
                )
            else:
                raise AIAPIError(
                    "API request failed: {}".format(str(e)),
                    status_code=status_code,
                    response=error_body
                )
        except URLError as e:
            if 'timed out' in str(e).lower():
                raise AITimeoutError(
                    "Request timed out after {} seconds".format(self.timeout)
                )
            raise AIAPIError("Network error: {}".format(str(e)))
        except Exception as e:
            raise AIAPIError("Unexpected error: {}".format(str(e)))

    def _parse_response(self, response):
        """Parse the AI API response.

        Args:
            response: API response dictionary.

        Returns:
            str: Extracted command or None.

        Raises:
            ParseError: On invalid response format.
        """
        try:
            choices = response.get('choices', [])
            if not choices:
                raise ParseError("No choices in API response")

            content = choices[0].get('message', {}).get('content', '')
            command = content.strip()

            # Check for inability to suggest
            if command == 'UNABLE_TO_SUGGEST' or not command:
                return None

            # Clean up common issues
            command = self._clean_command(command)

            return command
        except (KeyError, IndexError, TypeError) as e:
            raise ParseError("Failed to parse API response: {}".format(str(e)))

    def _clean_command(self, command):
        """Clean up command from AI response.

        Args:
            command: Raw command from AI.

        Returns:
            str: Cleaned command.
        """
        # Remove markdown code blocks
        command = re.sub(r'^```\w*\n?', '', command)
        command = re.sub(r'\n?```$', '', command)

        # Remove leading $ or > prompt
        command = re.sub(r'^[$>]\s*', '', command)

        # Strip whitespace
        command = command.strip()

        # Take only first line if multiple lines
        if '\n' in command:
            command = command.split('\n')[0].strip()

        return command


def generate_ai_command(user_request, context=None, failed_command=None,
                        error_output=None):
    """Convenience function to generate AI command.

    Args:
        user_request: What the user wants to do.
        context: Execution context.
        failed_command: Failed command if any.
        error_output: Error output if any.

    Returns:
        str: Suggested command or None.
    """
    provider = AIProvider()
    return provider.generate_command(user_request, context, failed_command,
                                     error_output)
