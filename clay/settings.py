"""
Application settings manager.
"""
from threading import Lock
import os
import copy
import errno
import yaml

import appdirs


class _SettingsEditor(dict):
    """
    Thread-safe settings editor context manager.

    For example see :py:meth:`~._Settings.edit`.
    """
    _lock = Lock()

    def __init__(self, original_config, commit_callback):
        super(_SettingsEditor, self).__init__()
        _SettingsEditor._lock.acquire()
        self._commit_callback = commit_callback
        self.update(copy.deepcopy(original_config))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        _SettingsEditor._lock.release()
        if exc_tb is None:
            self._commit_callback(self)
        else:
            # TODO: Handle this
            pass


class _Settings(object):
    """
    Settings management class.
    """
    def __init__(self):
        self._config = {}

        self._ensure_directories()
        self._load_config()

    def _ensure_directories(self):
        """
        Create config dir, config file & cache dir if they do not exist yet.
        """
        self._config_dir = appdirs.user_config_dir('clay', 'Clay')
        self._config_file_path = os.path.join(self._config_dir, 'config.yaml')

        try:
            os.makedirs(self._config_dir)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        self._cache_dir = appdirs.user_cache_dir('clay', 'Clay')
        try:
            os.makedirs(self._cache_dir)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        if not os.path.exists(self._config_file_path):
            with open(self._config_file_path, 'w') as settings_file:
                settings_file.write('{}')

    def _load_config(self):
        """
        Read config from file.
        """
        with open(self._config_file_path, 'r') as settings_file:
            self._config = yaml.load(settings_file.read())

    def _commit_edits(self, config):
        self._config.update(config)
        with open(self._config_file_path, 'w') as settings_file:
            settings_file.write(yaml.dump(self._config, default_flow_style=False))

    def get(self, key, default=None):
        """
        Return config value.
        """
        return self._config.get(key, default)

    def edit(self):
        """
        Return :py:class:`._SettingsEditor` context manager to edit config.

        Settings are saved to file once the returned context manager exists.

        Example usage:

        .. code-block:: python

            from clay.settings import settings

            with settings.edit() as config:
                config['foo']['bar'] = 'baz'
        """
        return _SettingsEditor(self._config, self._commit_edits)

    def get_cached_file_path(self, filename):
        """
        Get full path to cached file.
        """
        path = os.path.join(self._cache_dir, filename)
        if os.path.exists(path):
            return path
        return None

    def save_file_to_cache(self, filename, content):
        """
        Save content into file in cache.
        """
        path = os.path.join(self._cache_dir, filename)
        with open(path, 'wb') as cachefile:
            cachefile.write(content)
        return path


settings = _Settings()  # pylint: disable=invalid-name
