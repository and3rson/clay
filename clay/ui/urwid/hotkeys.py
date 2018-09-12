"""
Hotkeys management.
Requires "gi" package and "Gtk" & "Keybinder" modules.
"""
# pylint: disable=broad-except
from clay.core import settings_manager, logger

def report_error(exc):
    "Print an error message to the debug screen"
    logger.error("{0}: {1}".format(exc.__class__.__name__, exc))


class _HotkeyManager(object):
    """
    Manages configs.
    """
    def __init__(self):
        self._hotkeys = self._parse_hotkeys()
        self.config = None

    def _parse_hotkeys(self):
        """
        Reads out the configuration file and parse them into a hotkeys for urwid.
        """
        hotkey_config = settings_manager.get_default_config_section('hotkeys', 'clay_hotkeys')
        mod_key = settings_manager.get('mod_key', 'hotkeys')
        hotkeys = {}

        for hotkey_name, hotkey_dict in hotkey_config.items():
            hotkeys[hotkey_name] = {}
            for action in hotkey_dict.keys():
                key_seq = settings_manager.get(action, 'hotkeys', 'clay_hotkeys', hotkey_name)

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

hotkey_manager = _HotkeyManager()  # pylint: disable=invalid-name
