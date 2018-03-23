"""
Application settings manager.
"""
from threading import Lock
import os
import copy
import errno
import yaml
import appdirs
import pkg_resources


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
        self._default_config = {}
        self._cached_files = set()

        self._config_dir = None
        self._config_file_path = None
        self._cache_dir = None

        self._ensure_directories()
        self._load_config()
        self._load_cache()

    def _ensure_directories(self):
        """
        Create config dir, config file & cache dir if they do not exist yet.
        """
        self._config_dir = appdirs.user_config_dir('clay', 'Clay')
        self._config_file_path = os.path.join(self._config_dir, 'config.yaml')
        self._colours_file_path = os.path.join(self._config_dir, 'colours.yaml')

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

        # Load the configuration from Setuptools' ResourceManager API
        self._default_config = yaml.load(pkg_resources.resource_string(__name__, "config.yaml"))

        # We only either the user colour or the default colours to ease parsing logic.
        if os.path.exists(self._colours_file_path):
            with open(self._colours_file_path, 'r') as colours_file:
                self.colours_config = yaml.load(colours_file.read())
        else:
            self.colours_config = yaml.load(pkg_resources.resource_string(__name__, "colours.yaml"))


    def _load_cache(self):
        """
        Load cached files.
        """
        self._cached_files = set(os.listdir(self._cache_dir))

    def _commit_edits(self, config):
        """
        Write config to file.

        This method is supposed to be called only
        from :py:meth:`~._SettingsEditor.__exit__`.
        """
        self._config.update(config)
        with open(self._config_file_path, 'w') as settings_file:
            settings_file.write(yaml.dump(self._config, default_flow_style=False))

    def get(self, key, *sections):
        """
        Return their configuration key in a specified section
        By default it looks in play_settings.
        """
        section = self.get_section(*sections)

        try:
            return section.get(key)
        except (KeyError, TypeError):
            section = self.get_default_config_section(*sections)
            return section.get(key)

    def _get_section(self, config, *sections):
        config = config.copy()

        for section in sections:
            config = config[section]

        return config

    def get_section(self, *sections):
        """
        Get a section from the user configuration file if it can find it,
        else load it from the system config
        """
        try:
            return self._get_section(self._config, *sections)
        except (KeyError, TypeError):
            return self._get_section(self._default_config, *sections)


    def get_default_config_section(self, *sections):
        """
        Always get a section from the default/system configuration. You would use this whenever
        you need to loop through all the values in a section. In the user config they might be
        incomplete.
        """
        return self._get_section(self._default_config, *sections)

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

    def get_is_file_cached(self, filename):
        """
        Return ``True`` if *filename* is present in cache.
        """
        return filename in self._cached_files

    def save_file_to_cache(self, filename, content):
        """
        Save content into file in cache.
        """
        path = os.path.join(self._cache_dir, filename)
        with open(path, 'wb') as cachefile:
            cachefile.write(content)
        self._cached_files.add(filename)
        return path


settings = _Settings()  # pylint: disable=invalid-name
