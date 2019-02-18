"""
Generic page classes.
"""

import urwid

from clay.core import gp
from clay.ui.urwid import hotkey_manager, notification_area

class AbstractPage(object):
    """
    Represents app page.
    """

    @property
    def append(self):
        """
        Returns whether activate should append a song add the entire queue.
        """
        return False

    @property
    def name(self):
        """
        Return page name.
        """
        raise NotImplementedError()

    @property
    def key(self):
        """
        Return page key (``int``), used for hotkeys.
        """
        raise NotImplementedError()

    def activate(self):
        """
        Notify page that it is activated.
        """
        raise NotImplementedError()


class AbstractListItem(urwid.Columns):
    signals = ['activate']

    def __init__(self, value, icon):
        self._value = value
        self._icon = icon
        self.text = urwid.SelectableIcon('    {} {}'.format(self._icon, self._value))
        self.text.set_layout('left', 'clip', None)
        self.content = urwid.AttrWrap(self.text, 'default', 'selected')
        super(AbstractListItem, self).__init__([self.content])

    def keypress(self, size, key):
        return hotkey_manager.keypress("general_page", self, super(AbstractListItem, self), size, key)

    def activate(self):
        urwid.emit_signal(self, 'activate', self._value)


class AbstractListBox(urwid.ListBox):
    signals = ['activate']

    def __init__(self, app, placeholder='Loading...', icon=''):
        self.app = app
        self._icon = icon
        self.walker = urwid.SimpleListWalker([urwid.Text('\n ' + placeholder)])
        self.notification = None
        gp.auth_state_changed += self.auth_state_changed
        super(AbstractListBox, self).__init__(self.walker)

    def auth_state_changed(self, error):
        """
        Dummy function in case a list doesn't require authentication
        """
        pass

    def populate(self, values, error=None):
        if error:
            notification_area.notify("Failed to fetch {}: {}"
                                     .format(str(error), self.__class__.__name__))

        self._items = []

        for item in values:
            item = AbstractListItem(item, self._icon)
            urwid.connect_signal(item, 'activate', self.item_activated)
            self._items.append(item)

        self.walker[:] = self._items
        self.app.redraw()

    def item_activated(self, value):
        urwid.emit_signal(self, 'activate', value)
