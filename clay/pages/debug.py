"""
Debug page.
"""
import urwid

from clay.pages.page import AbstractPage
from clay.log import Logger
from clay.clipboard import copy


class DebugItem(urwid.AttrMap):
    """
    Represents a single debug log item.
    """
    def selectable(self):
        return True

    def __init__(self, log_record):
        self.log_record = log_record

        self.columns = urwid.Columns([
            ('pack', urwid.Text(self.log_record.verbosity.ljust(8))),
            urwid.Text(
                (
                    self.log_record.formatted_timestamp +
                    '\n' +
                    self.log_record.formatted_message
                )
            )
        ])

        super(DebugItem, self).__init__(self.columns, 'panel', 'panel_focus')

    def keypress(self, _, key):
        """
        Handle heypress.
        """
        if key == 'enter':
            copy(self.log_record.formatted_message)
            return None
        return key


class DebugPage(urwid.Pile, AbstractPage):
    """
    Represents debug page.
    """
    def __init__(self, app):
        self.app = app
        self.walker = urwid.SimpleListWalker([])
        for log_record in Logger.get().get_logs():
            self._append_log(log_record)
        Logger.get().on_log_event += self._append_log
        self.listbox = urwid.ListBox(self.walker)
        super(DebugPage, self).__init__([
            ('pack', urwid.Text('Hit "Enter" to copy selected message to clipboard.')),
            self.listbox
        ])

    def _append_log(self, log_record):
        self.walker.insert(0, urwid.Divider(u'\u2500'))
        self.walker.insert(0, DebugItem(log_record))

    @property
    def name(self):
        """
        Return page name.
        """
        return "Debug"

    @property
    def key(self):
        """
        Return page key (``int``), used for hotkeys.
        """
        return 0

    def activate(self):
        """
        Notify page that it is activated.
        """
        pass
