"""
Debug page.
"""
import urwid

from clay.pages.page import AbstractPage
from clay.log import logger
from clay.clipboard import copy
from clay.gp import gp
from clay.hotkeys import hotkey_manager


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

        super(DebugItem, self).__init__(self.columns, 'line1', 'line1_focus')

    def keypress(self, _, key):
        """
        Handle heypress.
        """
        return hotkey_manager.keypress("debug_page", self, None, None, key)

    def copy_message(self):
        """Copy the selected error message to the clipboard"""
        copy(self.log_record.formatted_message)
        return None


class DebugPage(urwid.Pile, AbstractPage):
    """
    Represents debug page.
    """
    def __init__(self, app):
        self.app = app
        self.walker = urwid.SimpleListWalker([])
        for log_record in logger.get_logs():
            self._append_log(log_record)
        logger.on_log_event += self._append_log
        self.listbox = urwid.ListBox(self.walker)

        self.debug_data = urwid.Text('')

        super(DebugPage, self).__init__([
            ('pack', self.debug_data),
            ('pack', urwid.Text('')),
            ('pack', urwid.Text('Hit "Enter" to copy selected message to clipboard.')),
            ('pack', urwid.Divider(u'\u2550')),
            self.listbox
        ])

        gp.auth_state_changed += self.update

        self.update()

    def update(self, *_):
        """
        Update this widget.
        """
        self.debug_data.set_text(
            '- Is authenticated: {}\n'
            '- Is subscribed: {}'.format(
                gp.is_authenticated,
                gp.is_subscribed if gp.is_authenticated else None
            )
        )

    def _append_log(self, log_record):
        """
        Add log record to list.
        """
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
