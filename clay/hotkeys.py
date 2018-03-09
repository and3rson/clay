"""
Hotkeys management.
Requires "gi" package and "Gtk" & "Keybinder" modules.
"""
# pylint: disable=broad-except
import threading

from clay.settings import settings
from clay.eventhook import EventHook
from clay.notifications import notification_area
from clay.log import logger


IS_INIT = False


def report_error(exc):
    "Print an error message to the debug screen"
    logger.error("{0}: {1}".format(exc.__class__.__name__, exc))


try:
    # pylint: disable=import-error
    import gi
    gi.require_version('Keybinder', '3.0')  # noqa
    gi.require_version('Gtk', '3.0')  # noqa
    from gi.repository import Keybinder, Gtk
    # pylint: enable=import-error
except ImportError as error:
    report_error(error)
    ERROR_MESSAGE = "Couldn't import PyGObject"
except ValueError as error:
    report_error(error)
    ERROR_MESSAGE = "Couldn't find the Keybinder and/or Gtk modules"
except Exception as error:
    report_error(error)
    ERROR_MESSAGE = "There was unknown error: '{}'".format(error)
else:
    IS_INIT = True


class _HotkeyManager(object):
    """
    Manages configs.
    Runs Gtk main loop in a thread.
    """
    def __init__(self):
        self._x_hotkeys = {}
        self._hotkeys = self._parse_hotkeys()
        self.config = None

        self.play_pause = EventHook()
        self.next = EventHook()
        self.prev = EventHook()

        if IS_INIT:
            Keybinder.init()
            self.initialize()
            threading.Thread(target=Gtk.main).start()
        else:
            logger.debug("Not loading the global shortcuts.")
            notification_area.notify(
                ERROR_MESSAGE +
                ", this means the global shortcuts will not work.\n" +
                "You can check the log for more details."
            )

    @staticmethod
    def _to_gtk_modifier(key):
        """
        Translates the modifies to the way that GTK likes them.
        """
        key = key.strip()

        if key == "meta":
            key = "<alt>"
        elif key in ("ctrl", "alt", "shift"):
            key = "<" + key + ">"
        else:
            key = key

        return key

    def _parse_x_hotkeys(self):
        """
        Reads out them configuration file and parses them into hotkeys readable by GTK.
        """
        hotkey_default_config = settings.get_default_config_section('hotkeys', 'x_hotkeys')
        mod_key = settings.get('mod_key', 'hotkeys')
        hotkeys = {}

        for action in hotkey_default_config:
            key_seq = settings.get(action, 'hotkeys', 'x_hotkeys')

            for key in key_seq.split(', '):
                hotkey = key.split(' + ')

                if hotkey[0].strip() == 'mod':
                    hotkey[0] = mod_key

                hotkey = [self._to_gtk_modifier(key) for key in hotkey]

                hotkeys[action] = ''.join(hotkey)

        return hotkeys

    def _parse_hotkeys(self):
        """
        Reads out the configuration file and parse them into a hotkeys for urwid.
        """
        hotkey_config = settings.get_default_config_section('hotkeys', 'clay_hotkeys')
        mod_key = settings.get('mod_key', 'hotkeys')
        hotkeys = {}

        for hotkey_name, hotkey_dict in hotkey_config.items():
            hotkeys[hotkey_name] = {}
            for action in hotkey_dict.keys():
                key_seq = settings.get(action, 'hotkeys', 'clay_hotkeys', hotkey_name)

                for key in key_seq.split(', '):
                    hotkey = key.split(' + ')

                    if hotkey[0].strip() == 'mod':
                        hotkey[0] = mod_key

                    hotkeys[hotkey_name][' '.join(hotkey)] = action
        return hotkeys

    def keypress(self, name, caller, super_, size, key):
        """
        Process the pressed key by looking it up in the configuration file

        """
        method_name = self._hotkeys[name].get(key)

        if method_name:
            ret = getattr(caller, method_name)()
        elif super_ is not None:
            ret = super_.keypress(size, key)
        else:
            ret = key

        return ret

    def initialize(self):
        """
        Unbind previous hotkeys, re-read config & bind new hotkeys.
        """
        for operation, key in self._x_hotkeys.items():
            Keybinder.unbind(key)

        self._x_hotkeys = self._parse_x_hotkeys()

        for operation, key in self._x_hotkeys.items():
            Keybinder.bind(key, self.fire_hook, operation)

    def fire_hook(self, key, operation):
        """
        Fire hook by name.
        """
        assert key
        getattr(self, operation).fire()


hotkey_manager = _HotkeyManager()  # pylint: disable=invalid-name
