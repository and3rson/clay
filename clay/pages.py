import urwid
from clay.settings import Settings
from clay.gp import gp
from clay.meta import VERSION
from clay.notifications import NotificationArea


class StartUp(urwid.Filler):
    def __init__(self, app):
        self.app = app

        super(StartUp, self).__init__(
            urwid.Pile([
                urwid.Padding(
                    urwid.AttrWrap(urwid.BigText(
                        'Clay'.format(VERSION),
                        urwid.font.HalfBlock5x4Font()
                    ), 'logo'),
                    'center',
                    None
                ),
                urwid.AttrWrap(urwid.Text('Version {}'.format(VERSION), align='center'), 'line1'),
                urwid.AttrWrap(urwid.Text('Authorizing...', align='center'), 'line2')
            ])
            # urwid.Text('Loading...'),
            # valign='top'
        )

        self.start()

    def on_login(self, success, error):
        if error:
            NotificationArea.notify('Failed to log in: {}'.format(str(error)))
            return

        if not success:
            NotificationArea.notify(
                'Google Play Music login failed '
                '(API returned false)'
            )
            return

        self.app.set_page('MyLibrary')

    def start(self):
        if Settings.is_config_valid():
            config = Settings.get_config()
            gp.login(
                config['username'],
                config['password'],
                config['device_id'],
                callback=self.on_login
            )
        else:
            NotificationArea.notify(
                'Please set your credentials on the settings page.'
            )

