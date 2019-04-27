"""
Hotkeys management.
Requires "gi" package and "Gtk" & "Keybinder" modules.
"""
# pylint: disable=broad-except
from clay.core import settings_manager, logger

from string import ascii_letters, digits

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
        self.filtering = False

    def _parse_hotkeys(self):
        """
        Reads out the configuration file and parse them into a hotkeys for urwid.
        """
        hotkey_config = settings_manager.get_default_config_section('hotkeys')
        mod_key = settings_manager.get('mod_key', 'clay_settings')
        hotkeys = {}

        for hotkey_name, hotkey_dict in hotkey_config.items():
            hotkeys[hotkey_name] = {}
            for action, sequence in hotkey_dict.items():
                key_seq = settings_manager.get(action, 'hotkeys', hotkey_name)

                if key_seq is None:
                    key_seq = sequence

                for key in key_seq.split(', '):
                    hotkey = key.split(' + ')

                    if hotkey[0].strip() == 'mod':
                        hotkey[0] = mod_key

                    hotkeys[hotkey_name][' '.join(hotkey)] = action

        return hotkeys

    def keypress(self, name, caller, super_, size, key):
        """
        Processes a key and sends the appropiated command back.

        Returns:
          the letter pressed if Clay is filtering, the command or, in case a modifier key is
          pressed, the command associated with the letter after the modifier key.
        """
        split_keys = key.split() if key != ' ' else key

        if split_keys[0] == 'meta' or split_keys[0] == 'ctrl':
            self.filtering = False
            return self._lookup_key(name, caller, super_, size, ''.join(split_keys[1:]))

        if not self.filtering:
            return self._lookup_key(name, caller, super_, size, key)

        if key == 'backspace' or key == 'tab' or key in ascii_letters + digits + ' _-.,?()[]\'':
            if name == 'song_view':
                ret = caller.perform_filtering(key)
            else:
                ret = super_.keypress(size, key)

        else:
            ret = self._lookup_key(name, caller, super_, size, key)

        return ret

    def _lookup_key(self, name, caller, super_, size, key):
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
