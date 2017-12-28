#!/usr/bin/env python3

from collections import OrderedDict

import urwid

from player import player
from pages import StartUp, Error
from mylibrary import MyLibrary
from myplaylists import MyPlaylists
from playerqueue import Queue
from settings import Settings


loop = None

PALETTE = [
    ('logo', '', '', '', '#F54', ''),

    ('bg', '', '', '', '#FFF', '#222'),
    ('primary', '', '', '', '#F54', '#FFF'),
    ('secondary', '', '', '', '#17F', '#FFF'),
    ('selected', '', '', '', '#FFF', '#444'),
    ('primary_inv', '', '', '', '#FFF', '#17F'),
    ('secondary_inv', '', '', '', '#FFF', '#F17'),
    ('progress', '', '', '', '#FFF', '#F54'),
    ('progress_remaining', '', '', '', '#FFF', '#444'),

    ('panel', '', '', '', '#FFF', '#222'),
    ('panel_focus', '', '', '', '#FFF', '#F54'),

    ('line1', '', '', '', '#FFF', ''),
    ('line1_focus', '', '', '', '#FFF', '#444'),
    ('line1_active', '', '', '', '#F54', ''),
    ('line1_active_focus', '', '', '', '#F54', '#444'),
    ('line2', '', '', '', '#AAA', ''),
    ('line2_focus', '', '', '', '#AAA', '#444'),

    ('input', '', '', '', '#FFF', '#444'),
    ('input_focus', '', '', '', '#FFF', '#F54'),
]


class PlayProgress(urwid.ProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.track = None

    def get_text(self):
        if self.track is None:
            return 'Idle'
        progress = player.get_play_progress_seconds()
        total = player.get_length_seconds()
        return '    {} - {} [{:02d}:{:02d} / {:02d}:{:02d}] {} {}'.format(
            self.track.artist,
            self.track.title,
            progress // 60,
            progress % 60,
            total // 60,
            total % 60,
            '' if player.get_is_random() else ' ',
            '' if player.get_is_repeat_one() else ' ',
        )

    def set_track(self, track):
        self.track = track

    def update(self):
        self._invalidate()


class AppWidget(urwid.Frame):
    class Tab(urwid.Text):
        def __init__(self, page_class):
            self.page_class = page_class
            # self.attrwrap = urwid.AttrWrap(urwid.Text(), 'panel')
            super().__init__(
                self.get_title()
            )

        def set_active(self, active):
            self.set_text(
                [('panel_focus' if active else 'panel', self.get_title())]
            )

        def get_title(self):
            return ' {} {} '.format(
                self.page_class.key,
                self.page_class.name
            )

    def __init__(self):
        self.pages = [
            StartUp,
            Error,
            MyLibrary,
            MyPlaylists,
            Queue,
            Settings
        ]
        self.tabs = [
            AppWidget.Tab(page_class)
            for page_class
            in [
                MyLibrary,
                MyPlaylists,
                Queue,
                Settings
            ]
        ]
        print(self.tabs)
        self.header = urwid.Pile([
            # urwid.Divider('\u2500'),
            urwid.AttrWrap(urwid.Columns([
                ('pack', tab)
                for tab
                in self.tabs
            ], dividechars=1), 'panel'),
            # urwid.Divider('\u2500')
        ])
        self.seekbar = PlayProgress(
            'progress_remaining',
            'progress',
            current=0,
            done=100,
            satt='bg'
        )
        self.panel = urwid.Pile([
            urwid.Divider('\u2500'),
            self.seekbar
        ])
        self.current_page = StartUp(self)
        super().__init__(
            header=self.header,
            footer=self.panel,
            body=self.current_page
        )

        player.media_position_changed += self.media_position_changed
        player.track_changed += self.track_changed
        player.playback_flags_changed += self.playback_flags_changed

    def media_position_changed(self, progress):
        if progress < 0:
            progress = 0
        self.seekbar.set_completion(progress * 100)
        loop.draw_screen()
        # sleep(0.2)

        # self.set_page(MyLibrary())

    def track_changed(self, track):
        self.seekbar.set_track(track)

    def playback_flags_changed(self):
        self.seekbar.update()

    def set_page(self, page_class, *args):
        if isinstance(page_class, str):
            page_class = [
                page
                for page
                in self.pages
                if page.__name__ == page_class
            ][0]
        self.current_page = page_class(self, *args)
        self.contents['body'] = (self.current_page, None)

        for tab in self.tabs:
            tab.set_active(False)
            if tab.page_class == page_class:
                tab.set_active(True)

        self.redraw()

    def redraw(self):
        if loop:
            loop.draw_screen()

    def keypress(self, size, key):
        if isinstance(self.current_page, StartUp):
            return
        for tab in self.tabs:
            if 'meta {}'.format(tab.page_class.key) == key:
                self.set_page(tab.page_class)
                return

        if key == 'ctrl w':
            player.play_pause()
        elif key == 'ctrl e':
            player.next(True)
        elif key == 'shift right':
            player.seek(0.05)
        elif key == 'shift left':
            player.seek(-0.05)
        elif key == 'ctrl s':
            player.set_random(not player.get_is_random())
        elif key == 'ctrl r':
            player.set_repeat_one(not player.get_is_repeat_one())
        else:
            super().keypress(size, key)


def main():
    global loop
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, PALETTE)
    loop.screen.set_terminal_properties(256)
    loop.run()


if __name__ == '__main__':
    main()

