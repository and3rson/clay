"""
Application settings manager.
"""
import os
import errno
import yaml

import appdirs


class Settings(object):
    """
    Settings management class.
    """
    @classmethod
    def get_config_filename(cls):
        """
        Return full path to config file.
        """
        filedir = appdirs.user_config_dir('clay', 'Clay')

        try:
            os.makedirs(filedir)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        try:
            os.makedirs(appdirs.user_cache_dir('clay', 'Clay'))
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        path = os.path.join(filedir, 'config.yaml')
        if not os.path.exists(path):
            with open(path, 'w') as settings:
                settings.write('{}')
        return path

    @classmethod
    def get_config(cls):
        """
        Read config dictionary.
        """
        with open(Settings.get_config_filename(), 'r') as settings:
            return yaml.load(settings.read())

    @classmethod
    def set_config(cls, new_config):
        """
        Write config dictionary.
        """
        config = Settings.get_config()
        config.update(new_config)
        with open(Settings.get_config_filename(), 'w') as settings:
            settings.write(yaml.dump(config, default_flow_style=False))

    @classmethod
    def get_cached_file_path(cls, filename):
        """
        Get full path to cached file.
        """
        cache_dir = appdirs.user_cache_dir('clay', 'Clay')
        path = os.path.join(cache_dir, filename)
        if os.path.exists(path):
            return path
        return None

    @classmethod
    def save_file_to_cache(cls, filename, content):
        """
        Save content into file in cache.
        """
        cache_dir = appdirs.user_cache_dir('clay', 'Clay')
        path = os.path.join(cache_dir, filename)
        with open(path, 'wb') as cachefile:
            cachefile.write(content)
        return path
