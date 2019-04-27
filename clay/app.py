#!/usr/bin/env python3
"""
The commandline startup script
"""
import os
import sys
sys.path.insert(0, '.')  # noqa

import argparse

from clay.core import meta, settings_manager
from clay.playback.player import get_player
import clay.ui.urwid as urwid


player = get_player()  # pylint: disable=invalid-name


class MultilineVersionAction(argparse.Action):
    """
    An argparser action for multiple lines so we can display the copyright notice
    Based on: https://stackoverflow.com/a/41147122
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        self.prog = os.path.basename(sys.argv[0])
        super(MultilineVersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=meta.COPYRIGHT_MESSAGE)


def main():
    """
    Starts the main clay process
    """
    try:
        from setproctitle import setproctitle
    except ImportError:
        pass
    else:
        setproctitle('clay')

    parser = argparse.ArgumentParser(
        prog=meta.APP_NAME,
        description=meta.DESCRIPTION,
        epilog="This project is neither affiliated nor endorsed by Google."
    )

    parser.add_argument("-v", "--version", action=MultilineVersionAction)

    args = parser.parse_args()

    if args.version:
        exit(0)

    urwid.main()


if __name__ == '__main__':
    main()
