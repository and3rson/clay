"""
Generic page classes.
"""


class AbstractPage(object):
    """
    Represents app page.
    """
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
