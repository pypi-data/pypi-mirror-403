import six
from ..conf import settings
from ..logs import warn
from ..shells import shell
from ..utils import which


def _get_alias(known_args):
    if six.PY2:
        warn("The Fuck will drop Python 2 support soon, more details "
             "https://github.com/nvbn/thefuck/issues/685")

    alias = shell.app_alias(known_args.alias)

    if known_args.enable_experimental_instant_mode:
        if six.PY2:
            warn("Instant mode requires Python 3")
        elif not which('script'):
            warn("Instant mode requires `script` app")
        else:
            return shell.instant_mode_alias(known_args.alias)

    return alias


def _get_ai_alias(known_args):
    """Get the AI command alias for the current shell."""
    ai_alias_name = getattr(settings, 'ai_trigger_word', None) or 'ai'
    return shell.ai_alias(ai_alias_name)


def print_alias(known_args):
    settings.init(known_args)
    # Print both the fuck alias and the ai alias
    print(_get_alias(known_args))
    print(_get_ai_alias(known_args))
