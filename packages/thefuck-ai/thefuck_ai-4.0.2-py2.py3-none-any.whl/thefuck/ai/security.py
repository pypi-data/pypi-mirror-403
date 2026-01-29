# -*- coding: utf-8 -*-
"""Security module for TheFuck-AI.

Provides command risk assessment and validation.
NOTE: All security checks are string-based pattern matching.
      NO commands are actually executed during security checks.
"""
import re
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration for commands."""
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    SAFE = 'SAFE'


class SecurityChecker:
    """Security checker for command validation.

    IMPORTANT: This class only performs string pattern matching.
    It does NOT execute any commands.
    """

    # High risk patterns - destructive or dangerous operations
    HIGH_RISK_PATTERNS = [
        # Destructive file operations
        r'\brm\s+(-[rf]+\s+)*[/~]',  # rm on root or home
        r'\brm\s+-rf\s+/',           # rm -rf /
        r'\brm\s+-rf\s+\*',          # rm -rf *
        r'>\s*/dev/sd[a-z]',         # overwrite disk
        r'dd\s+.*of=/dev/sd',        # dd to disk
        r'mkfs\.',                   # format filesystem

        # System modification
        r'\bchmod\s+(-R\s+)?777\s+/',  # chmod 777 on root
        r'\bchown\s+.*\s+/',  # chown on root
        r':\(\)\{\s*:\|:\s*&\s*\};:',  # fork bomb

        # Dangerous network operations
        r'\bcurl\s+.*\|\s*bash',     # curl | bash
        r'\bwget\s+.*\|\s*bash',     # wget | bash
        r'\bcurl\s+.*\|\s*sh',       # curl | sh
        r'\bwget\s+.*\|\s*sh',       # wget | sh

        # Credential/key operations
        r'\bsudo\s+su\s*$',          # sudo su without args
        r'\bpasswd\s+root',          # change root password
    ]

    # Medium risk patterns - potentially dangerous
    MEDIUM_RISK_PATTERNS = [
        # File operations that could be dangerous
        r'\brm\s+-rf\b',             # rm -rf (general)
        r'\brm\s+-r\b',              # rm -r (general)
        r'\brm\s+\*',                # rm *

        # Permission changes
        r'\bchmod\s+777\b',          # chmod 777
        r'\bchmod\s+-R\b',           # recursive chmod
        r'\bchown\s+-R\b',           # recursive chown

        # System services
        r'\bsystemctl\s+(stop|disable|mask)',
        r'\bservice\s+\w+\s+stop',

        # Package management (can change system state)
        r'\b(apt|yum|dnf|pacman)\s+(remove|purge)',
        r'\bpip\s+uninstall',
        r'\bnpm\s+uninstall\s+-g',

        # Process control
        r'\bkill\s+-9\b',            # force kill
        r'\bkillall\b',              # kill by name
        r'\bpkill\b',                # pattern kill
    ]

    # Low risk patterns - operations that modify state
    LOW_RISK_PATTERNS = [
        # File modifications
        r'\bmv\b',                   # move files
        r'\bcp\b',                   # copy files
        r'\btouch\b',                # create files
        r'\bmkdir\b',                # create directories

        # Git operations that modify state
        r'\bgit\s+push\b',
        r'\bgit\s+commit\b',
        r'\bgit\s+reset\b',
        r'\bgit\s+checkout\b',

        # Package installation
        r'\b(apt|yum|dnf|pacman)\s+install',
        r'\bpip\s+install\b',
        r'\bnpm\s+install\b',
    ]

    def __init__(self):
        """Initialize security checker with compiled patterns."""
        self._high_patterns = [re.compile(p, re.IGNORECASE)
                               for p in self.HIGH_RISK_PATTERNS]
        self._medium_patterns = [re.compile(p, re.IGNORECASE)
                                 for p in self.MEDIUM_RISK_PATTERNS]
        self._low_patterns = [re.compile(p, re.IGNORECASE)
                              for p in self.LOW_RISK_PATTERNS]

    def check(self, command):
        """Check the risk level of a command.

        NOTE: This is string pattern matching only.
              The command is NOT executed.

        Args:
            command: The command string to check.

        Returns:
            RiskLevel: The assessed risk level.
        """
        if not command or not isinstance(command, str):
            return RiskLevel.SAFE

        # Check high risk first
        for pattern in self._high_patterns:
            if pattern.search(command):
                return RiskLevel.HIGH

        # Check medium risk
        for pattern in self._medium_patterns:
            if pattern.search(command):
                return RiskLevel.MEDIUM

        # Check low risk
        for pattern in self._low_patterns:
            if pattern.search(command):
                return RiskLevel.LOW

        return RiskLevel.SAFE

    def get_risk_reasons(self, command):
        """Get reasons for the risk assessment.

        Args:
            command: The command to analyze.

        Returns:
            list: List of reason strings.
        """
        reasons = []

        if not command:
            return reasons

        # Check each pattern category
        for pattern in self._high_patterns:
            match = pattern.search(command)
            if match:
                reasons.append("High risk pattern: {}".format(
                    match.group()[:50]))

        for pattern in self._medium_patterns:
            match = pattern.search(command)
            if match:
                reasons.append("Medium risk pattern: {}".format(
                    match.group()[:50]))

        for pattern in self._low_patterns:
            match = pattern.search(command)
            if match:
                reasons.append("Low risk pattern: {}".format(
                    match.group()[:50]))

        return reasons

    def is_safe(self, command):
        """Check if command is safe (LOW or SAFE risk).

        Args:
            command: The command to check.

        Returns:
            bool: True if safe to execute.
        """
        risk = self.check(command)
        return risk in (RiskLevel.SAFE, RiskLevel.LOW)

    def requires_confirmation(self, command):
        """Check if command requires user confirmation.

        Args:
            command: The command to check.

        Returns:
            bool: True if confirmation is required.
        """
        risk = self.check(command)
        return risk in (RiskLevel.HIGH, RiskLevel.MEDIUM)


def check_command_safety(command):
    """Convenience function to check command safety.

    Args:
        command: The command to check.

    Returns:
        tuple: (RiskLevel, list of reasons)
    """
    checker = SecurityChecker()
    risk = checker.check(command)
    reasons = checker.get_risk_reasons(command)
    return risk, reasons
