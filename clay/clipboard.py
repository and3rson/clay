"""
Clipboard utils.
"""
from subprocess import Popen, PIPE

from clay.notifications import NotificationArea


COMMANDS = [
    ('xclip', '-selection', 'clipboard'),
    ('xsel', '-bi'),
]


def copy(text):
    """
    Copy text to clipboard.

    Return True on success.
    """
    for cmd in COMMANDS:
        proc = Popen(cmd, stdin=PIPE)
        proc.communicate(text.encode('utf-8'))
        if proc.returncode == 0:
            return True

    NotificationArea.notify(
        'Failed to copy text to clipboard. '
        'Please install "xclip" or "xsel".'
    )
    return False
