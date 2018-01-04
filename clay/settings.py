import os
import errno
import yaml

import appdirs

import urwid


class Settings(urwid.Columns):
    name = 'Settings'
    key = 9

    def __init__(self, app):
        self.app = app
        config = self.__class__.get_config()
        self.username = urwid.Edit(
            edit_text=config.get('username', '')
        )
        self.password = urwid.Edit(
            mask='*', edit_text=config.get('password', '')
        )
        self.device_id = urwid.Edit(
            edit_text=config.get('device_id', '')
        )
        return super(Settings, self).__init__([urwid.ListBox(urwid.SimpleListWalker([
            urwid.Text('Settings'),
            urwid.Divider(' '),
            urwid.Text('Username'),
            urwid.AttrWrap(self.username, 'input', 'input_focus'),
            urwid.Divider(' '),
            urwid.Text('Password'),
            urwid.AttrWrap(self.password, 'input', 'input_focus'),
            urwid.Divider(' '),
            urwid.Text('Device ID'),
            urwid.AttrWrap(self.device_id, 'input', 'input_focus'),
            urwid.Divider(' '),
            urwid.AttrWrap(urwid.Button(
                'Save', on_press=self.on_save
            ), 'input', 'input_focus')
        ]))])

    def on_save(self, button):
        self.__class__.set_config(dict(
            username=self.username.edit_text,
            password=self.password.edit_text,
            device_id=self.device_id.edit_text
        ))
        self.app.set_page('StartUp')
        # self.app.set_page('MyLibrary')

    @classmethod
    def get_config_filename(cls):
        filedir = appdirs.user_config_dir('clay', 'Clay')

        try:
            os.makedirs(filedir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        path = os.path.join(filedir, 'config.yaml')
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write('{}')
        return path

    @classmethod
    def get_config(cls):
        with open(cls.get_config_filename(), 'r') as f:
            return yaml.load(f.read())

    @classmethod
    def set_config(cls, new_config):
        config = cls.get_config()
        config.update(new_config)
        with open(cls.get_config_filename(), 'w') as f:
            f.write(yaml.dump(config, default_flow_style=False))

    @classmethod
    def is_config_valid(cls):
        config = cls.get_config()
        return all([
            config.get(x, None)
            for x
            in ('username', 'password', 'device_id')
        ])

