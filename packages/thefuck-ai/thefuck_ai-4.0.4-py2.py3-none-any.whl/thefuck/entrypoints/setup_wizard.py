# -*- coding: utf-8 -*-
"""Setup wizard for TheFuck-AI.

Interactive configuration wizard that guides users through API key setup.
"""
from __future__ import print_function
import sys
import os
import json

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from .. import const


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def colored(text, color):
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return "{}{}{}".format(color, text, Colors.END)
    return text


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ████████╗██╗  ██╗███████╗███████╗██╗   ██╗ ██████╗██╗  ║
║   ╚══██╔══╝██║  ██║██╔════╝██╔════╝██║   ██║██╔════╝██║  ║
║      ██║   ███████║█████╗  █████╗  ██║   ██║██║     ██║  ║
║      ██║   ██╔══██║██╔══╝  ██╔══╝  ██║   ██║██║     ██║  ║
║      ██║   ██║  ██║███████╗██║     ╚██████╔╝╚██████╗╚██╗ ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝  ╚═════╝ ╚═╝ ║
║                         -AI                              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    print(colored(banner, Colors.CYAN))
    print(colored("欢迎使用 TheFuck-AI 配置向导!", Colors.BOLD))
    print()


def get_user_dir():
    """Get user config directory."""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    user_dir = Path(xdg_config_home, 'thefuck').expanduser()
    legacy_user_dir = Path('~', '.thefuck').expanduser()

    if legacy_user_dir.is_dir():
        return legacy_user_dir
    return user_dir


def validate_api_key(api_key, endpoint=None, model=None):
    """Validate API key by making a test request.

    Args:
        api_key: The API key to validate.
        endpoint: API endpoint (optional).
        model: Model name (optional).

    Returns:
        tuple: (success: bool, message: str)
    """
    endpoint = endpoint or const.DEFAULT_SETTINGS['ai_endpoint']
    model = model or const.DEFAULT_SETTINGS['ai_model']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(api_key),
    }

    # Simple test request
    payload = {
        'model': model,
        'messages': [
            {'role': 'user', 'content': 'hi'},
        ],
        'max_tokens': 5,
    }

    data = json.dumps(payload).encode('utf-8')
    request = Request(endpoint, data=data, headers=headers)

    try:
        response = urlopen(request, timeout=15)
        result = json.loads(response.read().decode('utf-8'))

        if 'choices' in result:
            return True, "API Key 验证成功!"
        else:
            return False, "API 响应格式异常"

    except HTTPError as e:
        if e.code == 401:
            return False, "API Key 无效，请检查后重试"
        elif e.code == 403:
            return False, "API Key 权限不足"
        elif e.code == 429:
            # Rate limit means key is valid
            return True, "API Key 验证成功! (触发频率限制)"
        else:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                error_msg = error_body.get('error', {}).get('message', str(e))
            except Exception:
                error_msg = str(e)
            return False, "API 错误: {}".format(error_msg)
    except URLError as e:
        return False, "网络错误: {}".format(str(e))
    except Exception as e:
        return False, "验证失败: {}".format(str(e))


def write_config(user_dir, api_key, endpoint=None, model=None):
    """Write configuration to settings file.

    Args:
        user_dir: User config directory.
        api_key: API key to save.
        endpoint: API endpoint (optional).
        model: Model name (optional).

    Returns:
        tuple: (success: bool, message: str)
    """
    settings_path = user_dir.joinpath('settings.py')

    try:
        # Read existing settings if exists
        existing_content = ""
        if settings_path.is_file():
            with settings_path.open(mode='r') as f:
                existing_content = f.read()

        # Prepare new settings
        new_settings = []
        new_settings.append("ai_api_key = '{}'".format(api_key))

        if endpoint and endpoint != const.DEFAULT_SETTINGS['ai_endpoint']:
            new_settings.append("ai_endpoint = '{}'".format(endpoint))

        if model and model != const.DEFAULT_SETTINGS['ai_model']:
            new_settings.append("ai_model = '{}'".format(model))

        # Check if settings already exist and update them
        lines = existing_content.split('\n') if existing_content else []
        updated_keys = set()
        new_lines = []

        for line in lines:
            skip = False
            for setting in new_settings:
                key = setting.split('=')[0].strip()
                if line.strip().startswith(key) or line.strip().startswith('# ' + key):
                    if key not in updated_keys:
                        new_lines.append(setting)
                        updated_keys.add(key)
                    skip = True
                    break
            if not skip:
                new_lines.append(line)

        # Add new settings that weren't in the file
        for setting in new_settings:
            key = setting.split('=')[0].strip()
            if key not in updated_keys:
                new_lines.append(setting)

        # Write back
        content = '\n'.join(new_lines)
        if not content.endswith('\n'):
            content += '\n'

        # Ensure header exists
        if not content.startswith('#'):
            content = const.SETTINGS_HEADER + content

        with settings_path.open(mode='w') as f:
            f.write(content)

        return True, "配置已保存到 {}".format(settings_path)

    except Exception as e:
        return False, "保存配置失败: {}".format(str(e))


def prompt_input(prompt, default=None, password=False):
    """Prompt user for input.

    Args:
        prompt: Prompt text.
        default: Default value.
        password: If True, hide input.

    Returns:
        str: User input.
    """
    if default:
        prompt = "{} [{}]: ".format(prompt, default)
    else:
        prompt = "{}: ".format(prompt)

    try:
        if password:
            import getpass
            value = getpass.getpass(prompt)
        else:
            if sys.version_info[0] >= 3:
                value = input(prompt)
            else:
                value = raw_input(prompt)  # noqa: F821
    except (KeyboardInterrupt, EOFError):
        print()
        return None

    return value.strip() or default


def main():
    """Main setup wizard entry point."""
    print_banner()

    # Get user directory
    user_dir = get_user_dir()

    # Ensure directory exists
    if not user_dir.is_dir():
        try:
            user_dir.mkdir(parents=True)
        except Exception as e:
            print(colored("错误: 无法创建配置目录 {}".format(e), Colors.RED))
            sys.exit(1)

    print("配置文件位置: {}".format(colored(str(user_dir), Colors.CYAN)))
    print()

    # API Provider selection
    print(colored("步骤 1/3: 选择 AI 服务商", Colors.BOLD))
    print("  1. DeepSeek (默认)")
    print("  2. OpenAI 兼容接口 (自定义)")
    print()

    choice = prompt_input("请选择", "1")
    if choice is None:
        print(colored("\n已取消配置", Colors.YELLOW))
        sys.exit(0)

    if choice == "2":
        endpoint = prompt_input("API Endpoint")
        model = prompt_input("Model 名称")
        if not endpoint:
            print(colored("错误: Endpoint 不能为空", Colors.RED))
            sys.exit(1)
    else:
        endpoint = const.DEFAULT_SETTINGS['ai_endpoint']
        model = const.DEFAULT_SETTINGS['ai_model']

    print()

    # API Key input with retry
    print(colored("步骤 2/3: 输入 API Key", Colors.BOLD))
    if choice == "1":
        print("获取 DeepSeek API Key: https://platform.deepseek.com/api_keys")
    print()

    max_retries = 3
    for attempt in range(max_retries):
        api_key = prompt_input("API Key")

        if api_key is None:
            print(colored("\n已取消配置", Colors.YELLOW))
            sys.exit(0)

        if not api_key:
            print(colored("错误: API Key 不能为空", Colors.RED))
            continue

        # Validate
        print()
        print("正在验证 API Key...")
        success, message = validate_api_key(api_key, endpoint, model)

        if success:
            print(colored("✓ " + message, Colors.GREEN))
            break
        else:
            print(colored("✗ " + message, Colors.RED))
            remaining = max_retries - attempt - 1
            if remaining > 0:
                print("剩余重试次数: {}".format(remaining))
                print()
            else:
                print(colored("\n配置失败: 多次验证失败", Colors.RED))
                sys.exit(1)

    print()

    # Save configuration
    print(colored("步骤 3/3: 保存配置", Colors.BOLD))
    success, message = write_config(user_dir, api_key, endpoint, model)

    if success:
        print(colored("✓ " + message, Colors.GREEN))
    else:
        print(colored("✗ " + message, Colors.RED))
        sys.exit(1)

    print()
    print(colored("=" * 50, Colors.GREEN))
    print(colored("配置完成!", Colors.GREEN + Colors.BOLD))
    print()

    # Detect shell and show appropriate config
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        shell_config = '~/.zshrc'
        alias_cmd = 'eval $(thefuck --alias)'
    elif 'bash' in shell:
        shell_config = '~/.bashrc'
        alias_cmd = 'eval $(thefuck --alias)'
    elif 'fish' in shell:
        shell_config = '~/.config/fish/config.fish'
        alias_cmd = 'thefuck --alias | source'
    else:
        shell_config = '~/.bashrc 或 ~/.zshrc'
        alias_cmd = 'eval $(thefuck --alias)'

    print(colored("重要: 请完成以下步骤以启用 fuck 命令", Colors.YELLOW + Colors.BOLD))
    print()
    print("将以下内容添加到 " + colored(shell_config, Colors.CYAN) + ":")
    print()
    print(colored("  " + alias_cmd, Colors.GREEN))
    print()
    print("然后重新加载配置:")
    print(colored("  source " + shell_config, Colors.GREEN))
    print()
    print(colored("-" * 50, Colors.CYAN))
    print()
    print("可用命令:")
    print("  • " + colored("fuck", Colors.CYAN) + " - 自动修正上一条错误命令")
    print("  • " + colored("ai <你的需求>", Colors.CYAN) + " - 让 AI 生成命令")
    print()
    print("示例:")
    print("  $ lls")
    print("  zsh: command not found: lls")
    print("  $ fuck")
    print("  ls [enter/↑/↓/ctrl+c]")
    print()
    print("  $ ai 查看当前目录所有文件")
    print("  [AI] 执行: ls -la")
    print()


if __name__ == '__main__':
    main()
