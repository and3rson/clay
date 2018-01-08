"""
Initial startup page.
"""
# pylint: disable=too-many-ancestors
import urwid

from clay.page import Page
from clay.settings import SettingsPage
from clay.gp import GP
from clay.meta import VERSION
from clay.notifications import NotificationArea


class StartUpPage(urwid.Filler, Page):
    """
    Initial page.

    Shown when app is started or login credentials are changed.
    """
    def __init__(self, app):
        self.app = app

        super(StartUpPage, self).__init__(
            urwid.Pile([
                urwid.Padding(
                    urwid.AttrWrap(urwid.BigText(
                        'Clay',
                        urwid.font.HalfBlock5x4Font()
                    ), 'logo'),
                    'center',
                    None
                ),
                urwid.AttrWrap(urwid.Text('Version {}'.format(VERSION), align='center'), 'line1'),
                urwid.AttrWrap(urwid.Text('Authorizing...', align='center'), 'line2')
            ])
        )

    @property
    def name(self):
        pass

    @property
    def key(self):
        pass

    def on_login(self, success, error):
        """
        Called once user authorization finishes.
        If *error* is ``None``, switch app to "My library" page.'
        """
        if error:
            NotificationArea.notify('Failed to log in: {}'.format(str(error)))
            return

        if not success:
            NotificationArea.notify(
                'Google Play Music login failed '
                '(API returned false)'
            )
            return

        self.app.set_page('MyLibraryPage')

    def activate(self):
        """
        Called when this page is shown.

        Request user authorization.
        """
        if SettingsPage.is_config_valid():
            config = SettingsPage.get_config()
            GP.get().login_async(
                config['username'],
                config['password'],
                config['device_id'],
                callback=self.on_login
            )
        else:
            NotificationArea.notify(
                'Please set your credentials on the settings page.'
            )
