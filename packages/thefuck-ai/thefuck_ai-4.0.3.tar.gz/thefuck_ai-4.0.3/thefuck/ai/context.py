# -*- coding: utf-8 -*-
"""Context collection module for TheFuck-AI.

Collects execution environment context including:
- Current working directory
- System information (OS, shell, Python version)
- Command history (from shell history files)
- Environment variables (filtered for security)
"""
import os
import platform
import sys
from ..conf import settings


class ContextCollector:
    """Collects execution context for AI command generation."""

    # Environment variables that are safe to include
    SAFE_ENV_VARS = {
        'SHELL', 'TERM', 'LANG', 'LC_ALL', 'USER', 'HOME',
        'PWD', 'OLDPWD', 'PATH', 'EDITOR', 'VISUAL',
    }

    # Environment variables that should never be included
    SENSITIVE_ENV_PATTERNS = {
        'KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL',
        'AUTH', 'PRIVATE', 'API_KEY', 'AWS_', 'GITHUB_TOKEN',
    }

    def __init__(self):
        self._history_limit = settings.ai_history_limit or 5

    def collect(self):
        """Collect all context information.

        Returns:
            dict: Context dictionary with all collected information.
        """
        return {
            'cwd': self.get_cwd(),
            'system': self.get_system_info(),
            'history': self.get_history(),
            'env': self.get_safe_env(),
        }

    def get_cwd(self):
        """Get current working directory.

        Returns:
            str: Current working directory path.
        """
        try:
            return os.getcwd()
        except OSError:
            return None

    def get_system_info(self):
        """Get system information.

        Returns:
            dict: System information including OS, shell, python version.
        """
        shell = os.environ.get('SHELL', '')
        shell_name = os.path.basename(shell) if shell else 'unknown'

        return {
            'os': platform.system(),
            'os_version': platform.release(),
            'shell': shell_name,
            'python_version': sys.version.split()[0],
            'architecture': platform.machine(),
        }

    def get_history(self, limit=None):
        """Get recent command history from shell history file.

        Args:
            limit: Maximum number of history entries to return.

        Returns:
            list: Recent command history entries.
        """
        if limit is None:
            limit = self._history_limit

        shell = os.environ.get('SHELL', '')
        shell_name = os.path.basename(shell)

        history_file = self._get_history_file(shell_name)
        if not history_file or not os.path.exists(history_file):
            return []

        try:
            return self._read_history_file(history_file, shell_name, limit)
        except (IOError, OSError):
            return []

    def _get_history_file(self, shell_name):
        """Get the history file path for the current shell.

        Args:
            shell_name: Name of the shell (bash, zsh, etc.)

        Returns:
            str: Path to history file or None.
        """
        home = os.path.expanduser('~')

        history_files = {
            'bash': os.path.join(home, '.bash_history'),
            'zsh': os.path.join(home, '.zsh_history'),
            'fish': os.path.join(home, '.local', 'share', 'fish', 'fish_history'),
        }

        # Check for custom history file env vars
        if shell_name == 'bash' and 'HISTFILE' in os.environ:
            return os.environ['HISTFILE']
        if shell_name == 'zsh' and 'HISTFILE' in os.environ:
            return os.environ['HISTFILE']

        return history_files.get(shell_name)

    def _read_history_file(self, history_file, shell_name, limit):
        """Read history entries from file.

        Args:
            history_file: Path to history file.
            shell_name: Name of the shell.
            limit: Maximum entries to return.

        Returns:
            list: History entries.
        """
        with open(history_file, 'r', errors='ignore') as f:
            lines = f.readlines()

        # Parse based on shell format
        if shell_name == 'zsh':
            # zsh format: ": timestamp:0;command" or just "command"
            commands = []
            for line in lines:
                line = line.strip()
                if line.startswith(':') and ';' in line:
                    # Extended history format
                    cmd = line.split(';', 1)[1] if ';' in line else line
                    commands.append(cmd)
                elif line and not line.startswith('#'):
                    commands.append(line)
        else:
            # bash and others: simple line format
            commands = [line.strip() for line in lines
                        if line.strip() and not line.startswith('#')]

        # Return last N commands
        return commands[-limit:] if commands else []

    def get_safe_env(self):
        """Get safe environment variables (filtered).

        Returns:
            dict: Safe environment variables.
        """
        safe_env = {}

        for key, value in os.environ.items():
            if self._is_safe_env_var(key):
                safe_env[key] = value

        return safe_env

    def _is_safe_env_var(self, key):
        """Check if environment variable is safe to include.

        Args:
            key: Environment variable name.

        Returns:
            bool: True if safe to include.
        """
        key_upper = key.upper()

        # Check if explicitly safe
        if key in self.SAFE_ENV_VARS:
            return True

        # Check for sensitive patterns
        for pattern in self.SENSITIVE_ENV_PATTERNS:
            if pattern in key_upper:
                return False

        return False  # Default to not including unknown vars


def collect_context():
    """Convenience function to collect context.

    Returns:
        dict: Collected context.
    """
    collector = ContextCollector()
    return collector.collect()
