"""
Components for "Settings" page.
"""
import urwid

from clay.pages.page import AbstractPage
from clay.settings import Settings


class SettingsPage(urwid.Columns, AbstractPage):
    """
    Settings page.
    """
    @property
    def name(self):
        return 'Settings'

    @property
    def key(self):
        return 9

    def __init__(self, app):
        self.app = app
        config = Settings.get_config()
        self.username = urwid.Edit(
            edit_text=config.get('username', '')
        )
        self.password = urwid.Edit(
            mask='*', edit_text=config.get('password', '')
        )
        self.device_id = urwid.Edit(
            edit_text=config.get('device_id', '')
        )
        super(SettingsPage, self).__init__([urwid.ListBox(urwid.SimpleListWalker([
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

    def on_save(self, *_):
        """
        Called when "Save" button is pressed.
        """
        Settings.set_config(dict(
            username=self.username.edit_text,
            password=self.password.edit_text,
            device_id=self.device_id.edit_text
        ))
        self.app.set_page('MyLibraryPage')
        self.app.log_in()

    def activate(self):
        pass
