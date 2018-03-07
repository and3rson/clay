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
        self.hotkeys = {}
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

    def _parse_hotkeys(self):
        """
        Read out the configuration file and parse them into a dictionary readable for urwid.
        """
        hotkey_config = settings.get_default_config_section('hotkeys', 'clay_hotkeys')
        mod_key = settings.get('mod_key', 'hotkeys')
        hotkeys = {}

        for hotkey_name, hotkey_dict in hotkey_config.items():
            hotkeys[hotkey_name] = {}
            for action in hotkey_dict.keys():
                key_seq = settings.get(action, 'hotkeys', 'clay_hotkeys', hotkey_name)\
                                  .replace(' ', '')

                for key in key_seq.split(','):
                    hotkey = key.split('+') if key != '+' else key

                    if hotkey[0] == 'mod':
                        hotkey[0] = mod_key

                    hotkeys[hotkey_name][' '.join(hotkey)] = action

        return hotkeys

    @staticmethod
    def load_keys():
        """
        Load hotkey config from settings.
        """
        hotkeys = settings.get_section('hotkeys', 'x_hotkeys')
        default_hotkeys = settings.get_default_config_section('hotkeys', 'x_hotkeys')

        if hotkeys is default_hotkeys:
            return default_hotkeys

        for operation, default_key in default_hotkeys.items():
            if operation not in hotkeys:
                hotkeys[operation] = default_key

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


hotkey_manager = _HotkeyManager()  # pylint: disable=invalid-name
