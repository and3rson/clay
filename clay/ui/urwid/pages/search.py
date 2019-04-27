"""
Components for search page.
"""
import urwid

from .page import AbstractPage
from clay.core import gp
from clay.ui.urwid import SongListBox, notification_area, hotkey_manager


class ArtistListBox(urwid.ListBox):
    """
    Widget that displays list of artists.
    """
    def __init__(self):
        self.walker = urwid.SimpleListWalker([])
        super(ArtistListBox, self).__init__(self.walker)


class SearchBox(urwid.Columns):
    """
    Widget that displays search input and results.
    """
    signals = ['search-requested']

    def __init__(self):
        self.query = urwid.Edit()
        super(SearchBox, self).__init__([
            ('pack', urwid.Text('Search: ')),
            urwid.AttrWrap(self.query, 'input', 'input_focus')
        ])

    def keypress(self, size, key):
        """
        Handle keypress.
        """
        return hotkey_manager.keypress("search_page", self, super(SearchBox, self), size, key)

    def send_query(self):
        """
        Send a message to urwid to search the filled in search query
        """

        urwid.emit_signal(self, 'search-requested', self.query.edit_text)


class SearchPage(urwid.Pile, AbstractPage):
    """
    Search page.

    Allows to perform searches & displays search results.
    """
    @property
    def append(self):
        return True

    @property
    def name(self):
        return 'Search'

    @property
    def key(self):
        return 6

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "search"

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)
        self._focus_position = 0
        self.search_box = SearchBox()

        urwid.connect_signal(self.search_box, 'search-requested', self.perform_search)

        super(SearchPage, self).__init__([
            ('pack', self.search_box),
            ('pack', urwid.Divider(u'\u2500')),
            self.songlist
        ])

    def perform_search(self, query):
        """
        Search tracks by query.
        """
        self.songlist.set_placeholder(u' \U0001F50D Searching for "{}"...'.format(
            query
        ))
        gp.search_async(query, callback=self.search_finished)

    def search_finished(self, results, error):
        """
        Populate song list with search results.
        """
        if error:
            notification_area.notify('Failed to search: {}'.format(str(error)))
        else:
            self.songlist.populate(results.get_tracks())
            self.app.redraw()

    def activate(self):
        hotkey_manager.filtering = True

    def keypress(self, size, key):
        hotkey_manager.filtering = (self.focus == self.search_box)

        if key == 'tab':
            if self.focus == self.search_box:
                self.focus_position = 2
            else:
                self.focus_position = 0
            return None
        return super(SearchPage, self).keypress(size, key)
