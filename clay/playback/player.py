import importlib

from clay.core.settings import settings_manager

_PLAYER = None


def get_player():
    global _PLAYER
    if _PLAYER is None:
        player_import_str = settings_manager.get('player_class', 'clay_settings')
        if player_import_str is None:
            player_import_str = 'clay.playback.vlc:VLCPlayer'

        player_module, _, player_var = player_import_str.rpartition(':')

        module = importlib.import_module(player_module)
        player_class = getattr(module, player_var)
        _PLAYER = player_class()
    return _PLAYER
