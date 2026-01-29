# -*- coding: utf-8 -*-
"""AI command entry point for TheFuck-AI."""
import os
import sys
from .. import logs
from ..conf import settings
from ..ai.ai_command import AICommand


def main():
    """Standalone entry point for 'ai' command."""
    from ..argument_parser import Parser
    parser = Parser()
    # Parse with ai=True to get command arguments
    known_args = parser.parse(sys.argv)
    known_args.ai = True
    ai_command(known_args)


def ai_command(known_args):
    """Process AI command request.

    Args:
        known_args: Parsed command line arguments.
    """
    # Initialize settings (load from file and env)
    settings.init(known_args)

    # Get user request from remaining arguments
    user_request = ' '.join(known_args.command) if known_args.command else ''

    # Context mode: if no request, try to get last failed command
    failed_command = None
    error_output = None
    if not user_request:
        # Try to get last command from TF_HISTORY
        history = os.environ.get('TF_HISTORY', '')
        if history:
            lines = [line.strip() for line in history.strip().split('\n') if line.strip()]
            if lines:
                failed_command = lines[-1]
                user_request = "修复这个命令: " + failed_command

        if not user_request:
            logs.warn("[AI] 请输入您的需求")
            logs.warn("用法: ai <您的需求>")
            logs.warn("示例: ai 查看当前目录所有文件")
            return

    # Show analyzing message to stderr (won't interfere with command output)
    sys.stderr.write("[AI] 分析中...\n")
    sys.stderr.flush()

    handler = AICommand()
    result = handler.process(user_request, failed_command=failed_command,
                             error_output=error_output)

    if result.get('error'):
        logs.warn("[AI] " + result['error'])
        return

    command = result.get('command')
    if not command:
        logs.warn("[AI] 无法生成命令，请重新描述您的需求")
        return

    # Prevent infinite loop: block if AI returns 'ai' command
    trigger_word = settings.ai_trigger_word or 'ai'
    cmd_first_word = command.strip().split()[0] if command.strip() else ''
    if cmd_first_word.lower() == trigger_word.lower():
        logs.warn("[AI] 无法理解您的请求，请用更具体的描述")
        logs.warn("示例: ai 列出当前目录的文件")
        return

    risk_level = result.get('risk_level')
    blocked = result.get('blocked', False)

    if blocked:
        logs.warn("[安全] 此命令被禁止执行（高危操作）: {}".format(command))
        if result.get('reasons'):
            for reason in result['reasons']:
                logs.warn("  - {}".format(reason))
        logs.warn("[AI] 建议：请明确指定安全的操作范围")
        return

    # Output format: RISK_LEVEL:COMMAND
    # This allows shell alias to handle differently based on risk
    risk_str = risk_level.value if risk_level else 'SAFE'
    sys.stdout.write("{}:{}".format(risk_str, command))
    sys.stdout.flush()
