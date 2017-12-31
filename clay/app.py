#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

import urwid

from clay.player import player
from clay.widgets import PlayProgress
from clay.pages import StartUp, Error
from clay.mylibrary import MyLibrary
from clay.myplaylists import MyPlaylists
from clay.playerqueue import Queue
from clay.settings import Settings
# from clay import hotkeys


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

    ('flag', '', '', '', '#AAA', ''),
    ('flag-active', '', '', '', '#F54', ''),
]


class AppWidget(urwid.Frame):
    class Tab(urwid.Text):
        def __init__(self, page_class):
            self.page_class = page_class
            # self.attrwrap = urwid.AttrWrap(urwid.Text(), 'panel')
            super(AppWidget.Tab, self).__init__(
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
            done=100
        )
        self.shuffle_el = urwid.AttrWrap(urwid.Text(' ⋍ SHUF '), 'flag')
        self.repeat_el = urwid.AttrWrap(urwid.Text(' ⟲ REP '), 'flag')
        self.panel = urwid.Pile([
            urwid.Columns([
                urwid.Divider('\u2500'),
                ('pack', self.shuffle_el),
                # ('pack', urwid.Text(' ')),
                ('pack', self.repeat_el)
            ]),
            self.seekbar
        ])
        self.current_page = StartUp(self)
        super(AppWidget, self).__init__(
            header=self.header,
            footer=self.panel,
            body=self.current_page
        )

        player.media_position_changed += self.media_position_changed
        player.media_state_changed += self.media_state_changed
        player.track_changed += self.track_changed
        player.playback_flags_changed += self.playback_flags_changed

    def media_position_changed(self, progress):
        if progress < 0:
            progress = 0
        self.seekbar.set_completion(progress * 100)
        loop.draw_screen()
        # sleep(0.2)

        # self.set_page(MyLibrary())

    def media_state_changed(self, is_playing):
        self.seekbar.update()

    def track_changed(self, track):
        self.seekbar.set_track(track)

    def playback_flags_changed(self):
        self.shuffle_el.attr = 'flag-active' \
            if player.get_is_random() \
            else 'flag'
        self.repeat_el.attr = 'flag-active' \
            if player.get_is_repeat_one() \
            else 'flag'
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

        if key == 'ctrl q':
            player.seek_absolute(0)
        elif key == 'ctrl w':
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
        elif key == 'ctrl q':
            sys.exit(0)
        else:
            super(AppWidget, self).keypress(size, key)


def main():
    global loop
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, PALETTE)
    loop.screen.set_terminal_properties(256)
    loop.run()


if __name__ == '__main__':
    main()

