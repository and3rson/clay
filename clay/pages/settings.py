"""
Components for "Settings" page.
"""
import urwid

from clay.pages.page import AbstractPage
from clay.settings import Settings
from clay.player import Player


class Slider(urwid.Widget):
    """
    Represents a (TODO: vertical) slider for equalizer band modification.
    TODO: Save equalizer settings in config file.
    """
    _sizing = frozenset([urwid.FLOW])

    CHARS = [
        # '_',
        u'\u2581',
        u'\u2500',
        u'\u2594'
    ]

    def selectable(self):
        return True

    def __init__(self, index, freq):
        self.index = index
        if int(freq) == freq:
            freq = int(freq)
        self.freq = freq
        if freq >= 1000:
            self.freq_str = str(freq // 1000) + ' KHz'
        else:
            self.freq_str = str(freq) + ' Hz'
        self.value = 0
        self.slider_height = 5
        self.max_value = 20
        super(Slider, self).__init__()

    def rows(self, *_):
        """
        Return count of rows required to render this widget.
        """
        return self.slider_height + 2

    def render(self, size, focus=None):
        """
        Render widget.
        """
        rows = [('+' if self.value >= 0 else '') + str(self.value) + ' dB']

        chars = [' '] * 5

        k = ((float(self.value) / (self.max_value + 1)) + 1) / 2  # Convert value to [0;1] range
        section_index = int(k * self.slider_height)
        char_index = int(k * self.slider_height * len(Slider.CHARS)) % len(Slider.CHARS)
        chars[section_index] = Slider.CHARS[char_index]

        # rows.extend(['X'] * self.slider_height)
        rows.extend([
            (
                u'\u2524{}\u251C'
                if i == self.slider_height // 2
                else u'\u2502{}\u2502'
            ).format(x)
            for i, x
            in enumerate(reversed(chars))
        ])
        rows.append(self.freq_str)
        text = urwid.AttrMap(urwid.Text('\n'.join(
            rows
        ), align=urwid.CENTER), 'default', 'panel_focus')
        return text.render(size, focus)

    def keypress(self, _, key):
        """
        Handle equalizer band modification.
        """
        if key == '+':
            if self.value < self.max_value:
                self.value += 1
                self.update()
            return None
        elif key == '-':
            if self.value > -self.max_value:
                self.value -= 1
                self.update()
            return None
        else:
            return key

    def update(self):
        """
        Update player equalizer & toggle redraw.
        """
        Player.get().set_equalizer_value(self.index, self.value)
        self._invalidate()


class Equalizer(urwid.Columns):
    """
    Represents an equalizer.
    """
    def __init__(self):
        self.bands = [
            Slider(index, freq)
            for index, freq
            in enumerate(Player.get().get_equalizer_freqs())
        ]
        super(Equalizer, self).__init__(
            self.bands
        )


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
        self.download_tracks = urwid.CheckBox(
            'Download tracks before playback',
            state=config.get('download_tracks', False)
        )
        self.equalizer = Equalizer()
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
            self.download_tracks,
            urwid.Divider(' '),
            urwid.AttrWrap(urwid.Button(
                'Save', on_press=self.on_save
            ), 'input', 'input_focus'),
            urwid.Divider(u'\u2500'),
            self.equalizer,
        ]))])

    def on_save(self, *_):
        """
        Called when "Save" button is pressed.
        """
        Settings.set_config(dict(
            username=self.username.edit_text,
            password=self.password.edit_text,
            device_id=self.device_id.edit_text,
            download_tracks=self.download_tracks.state
        ))
        self.app.set_page('MyLibraryPage')
        self.app.log_in()

    def activate(self):
        pass
