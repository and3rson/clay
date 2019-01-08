"""
On-screen display stuff.
"""
from pydbus import SessionBus, Variant
from clay.core import meta, logger, settings_manager
from gi.repository import GLib

NOTIFICATION_BUS_NAME = ".Notifications"
BASE_NAME = "org.freedesktop"
ENABLED = settings_manager.get('desktop_notifications', 'clay_settings')


class _OSDManager(object):
    """
    Manages OSD notifications via DBus.
    """
    def __init__(self):
        if not ENABLED:
            self._actions = {}
            return

        self._last_id = 0
        self.bus = SessionBus()

        self.notifications = None
        self.bus.watch_name(BASE_NAME + NOTIFICATION_BUS_NAME,
                            name_appeared=self._register_bus_name,
                            name_vanished=self._deregister_bus_name)
        self._register_bus_name(None)

        self._actions = {"default": lambda *args: None}

    def add_to_action(self, action, action_name, function):
        """
        Register an action to the notification deamon
        Note: you can override the default action by passing "default" the action argument.
        Note: by passing the same action argument you override it.

        Args:
           action (`str`): The action that you want to invoke.
           action_name (`str`): The human readable string that describes the action
           function (`func`): The function that you want to envoke when it is called
        """
        self._actions[action] = (action_name, function)

    def notify(self, title, body, actions, icon, replace=True):
        """
        Create new or update existing notification.

        Args:
           track (`clay.gp.Track`): The track that you want to send the notification for
           actions (`list`): A list with the actions that you want the notification to react to.
        """
        if not ENABLED:
            return

        actions_ = []
        for action in actions:
            if action not in self._actions:
                logger.error("Can't find action: {}".format(action))
                continue

            actions_.append(action)
            actions_.append(self._actions[action][0])

        self._notify(title, body, replace, actions=actions_,
                     hints={"action-icons": Variant('b', 1)},  # only display icons
                     icon=icon if icon is not None else 'audio-headphones')

    def _on_action(self, id_, action):
        if id_ != self._last_id:
            return

        if action in self._actions:
            self._actions[action][1]()
        else:
            self._actions.get("default")[1]()

    def _notify(self, summary, body, replace=True, actions=None, hints=None, expiration=5000,
                icon='audio-headphones'):
        """
        An implementation of Desktop Notifications Specification 1.2.
        For a detailed explanation see: https://developer.gnome.org/notification-spec/

        Does not fire if notifications were not properly set up
        Args:
           summary (`str`): A single line overview of the notification
           body (`str`): A mutli-line body of the text
           replace (`bool`): Should the notification be updated or should a new one be made
           actions (`list`): The actions a notification can perform, might be ignored. Default empty
           hints (`dict`): Extra information the server might be able to make use of
           expiration (`int`): The time until the notification automatically closes. -1 to make the
              server decide and 0 for never. Defaults to 5000.
           icon (`str`): The string to icon it displays in the notification. Defaults to headbuds.

        Returns:
           Nothing.
        """
        if self.notifications is None:
            return

        try:
            self._last_id = self.notifications.Notify(meta.APP_NAME, self._last_id if replace else 0,
                                                      icon, summary, body,
                                                      actions if actions is not None else list(),
                                                      hints if hints is not None else dict(),
                                                      expiration)
        except GLib.Error as exception:
            logger.error('Failed to post notification %s', exception)

    def _register_bus_name(self, name_owner):
        """
        Registers a bus for sending notifications over dbus

        Args:
            name_owner (`str`) (unused): The owner of the bus

        Returns:
            Nothing.
        """
        try:
            self.notifications = self.bus.get(NOTIFICATION_BUS_NAME)
            self.notifications.onActionInvoked = self._on_action
        except GLib.Error:
            # Bus name did not exist
            logger.error('Attempted bus name registration failed, %s', NOTIFICATION_BUS_NAME)

    def _deregister_bus_name(self):
        """
        Deregisters a bus for sending notifications over dbus.
        Once run, notifications cannot be sent

        Returns:
            Nothing.
        """
        self.notifications = None


osd_manager = _OSDManager()  # pylint: disable=invalid-name
