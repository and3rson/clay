import sys
import threading

try:
    import gi
    gi.require_version('Keybinder', '3.0')  # noqa
    gi.require_version('Gtk', '3.0')  # noqa
    from gi.repository import Keybinder, Gtk
except Exception as e:
    sys.stderr.write('Could not import Keybinder and Gtk. Error was: "{}"\n'.format(e))
    sys.stderr.write('Global shortcuts will not work.\n')
    IS_INIT = False
    ERROR = str(e)
else:
    IS_INIT = True

from clay.settings import Settings
from clay.eventhook import EventHook
from clay.notifications import NotificationArea


class HotkeyManager(object):
    DEFAULT_HOTKEYS = {
        'play_pause': 'XF86AudioPlay',
        'next': 'XF86AudioNext',
        'prev': 'XF86AudioPrev'
    }

    def __init__(self):
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

    def load_keys(self):
        config = Settings.get_config()
        hotkeys = config.get('hotkeys', {})
        for op, default_key in HotkeyManager.DEFAULT_HOTKEYS.items():
            if op not in hotkeys or not hotkeys[op]:
                hotkeys[op] = default_key
        return hotkeys

    def initialize(self):
        for op, key in self.hotkeys.items():
            Keybinder.unbind(key)
        self.hotkeys = self.load_keys()
        for op, key in self.hotkeys.items():
            Keybinder.bind(key, self.fire_hook, op)

    def fire_hook(self, key, op):
        getattr(self, op).fire()


hotkey_manager = HotkeyManager()

