"""
Hotkeys management.
Requires "gi" package and "Gtk" & "Keybinder" modules.
"""
# pylint: disable=broad-except
import sys
import threading

try:
    # pylint: disable=import-error
    import gi
    gi.require_version('Keybinder', '3.0')  # noqa
    gi.require_version('Gtk', '3.0')  # noqa
    from gi.repository import Keybinder, Gtk
    # pylint: enable=import-error
except Exception as error:
    sys.stderr.write('Could not import Keybinder and Gtk. Error was: "{}"\n'.format(error))
    sys.stderr.write('Global shortcuts will not work.\n')
    IS_INIT = False
    ERROR = str(error)
else:
    IS_INIT = True

from clay.settings import Settings
from clay.eventhook import EventHook
from clay.notifications import NotificationArea


class HotkeyManager(object):
    """
    Manages configs.
    Runs Gtk main loop in a thread.
    """
    DEFAULT_HOTKEYS = {
        'play_pause': 'XF86AudioPlay',
        'next': 'XF86AudioNext',
        'prev': 'XF86AudioPrev'
    }

    instance = None

    def __init__(self):
        assert self.__class__.instance is None, 'Can be created only once!'
        self.hotkeys = {}
        self.config = None

        self.play_pause = EventHook()
        self.next = EventHook()
        self.prev = EventHook()

        if IS_INIT:
            Keybinder.init()
            self.initialize()

            threading.Thread(target=Gtk.main).start()
        else:
            NotificationArea.notify(
                'Could not import Keybinder and Gtk. Error was: "{}"\n'
                'Global shortcuts will not work.'.format(ERROR)
            )

    @classmethod
    def get(cls):
        """
        Create new :class:`.HotkeyManager` instance or return existing one.
        """
        if cls.instance is None:
            cls.instance = HotkeyManager()

        return cls.instance

    @staticmethod
    def load_keys():
        """
        Load hotkey config from settings.
        """
        config = Settings.get_config()
        hotkeys = config.get('hotkeys', {})
        for operation, default_key in HotkeyManager.DEFAULT_HOTKEYS.items():
            if operation not in hotkeys or not hotkeys[operation]:
                hotkeys[operation] = default_key
        return hotkeys

    def initialize(self):
        """
        Unbind previous hotkeys, re-read config & bind new hotkeys.
        """
        for operation, key in self.hotkeys.items():
            Keybinder.unbind(key)
        self.hotkeys = self.load_keys()
        for operation, key in self.hotkeys.items():
            Keybinder.bind(key, self.fire_hook, operation)

    def fire_hook(self, key, operation):
        """
        Fire hook by name.
        """
        assert key
        getattr(self, operation).fire()
