"""
Application settings manager.
"""
import os
import errno
import yaml
import appdirs


# Rewrite this so it keeps the settings in memory and writes on exit
# It is sort of silly to use so much IO for simple tasks
class Settings(object):
    """
    Settings management class.
    """
    @classmethod
    def get_config_filename(cls):
        """
        Returns full path to config file and will create it if it doesn't
        already exist.
        """
        filedir = appdirs.user_config_dir('clay', 'Clay')
        path = os.path.join(filedir, 'config.yaml')

        if os.path.exists(path):
            return path

        try:
            os.makedirs(filedir)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        with open(path, 'w') as settings:
            settings.write('{}')

        return path

    @classmethod
    def get_config(cls, section):
        """
        Read config dictionary.
        """
        with open(Settings.get_config_filename(), 'r') as settings:
            return yaml.load(settings.read()).get(section)

    @classmethod
    def set_config(cls, new_config):
        """
        Write config dictionary.
        """
        config = Settings.get_config('play_settings')
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
