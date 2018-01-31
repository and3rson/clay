"""
Logger implementation.
"""
# pylint: disable=too-few-public-methods
from threading import Lock
from datetime import datetime

from clay.eventhook import EventHook


class LoggerRecord(object):
    """
    Represents a logger record.
    """
    def __init__(self, verbosity, message, args):
        self._timestamp = datetime.now()
        self._verbosity = verbosity
        self._message = message
        self._args = args

    @property
    def formatted_timestamp(self):
        """
        Return timestamp.
        """
        return str(self._timestamp)

    @property
    def verbosity(self):
        """
        Return verbosity.
        """
        return self._verbosity

    @property
    def formatted_message(self):
        """
        Return formatted message.
        """
        return self._message % self._args


class Logger(object):
    """
    Global logger.

    Allows subscribing to log events.
    """
    instance = None

    def __init__(self):
        assert self.__class__.instance is None, 'Can be created only once!'

        self.logs = []
        self.logfile = open('/tmp/clay.log', 'w')

        self._lock = Lock()

        self.on_log_event = EventHook()

    @classmethod
    def get(cls):
        """
        Create new :class:`.Logger` instance or return existing one.
        """
        if cls.instance is None:
            cls.instance = Logger()

        return cls.instance

    def log(self, level, message, *args):
        """
        Add log item.
        """
        self._lock.acquire()
        try:
            logger_record = LoggerRecord(level, message, args)
            self.logs.append(logger_record)
            self.logfile.write('{} {:8} {}\n'.format(
                logger_record.formatted_timestamp,
                logger_record.verbosity,
                logger_record.formatted_message
            ))
            self.logfile.flush()
            self.on_log_event.fire(logger_record)
        finally:
            self._lock.release()

    def debug(self, message, *args):
        """
        Add debug log item.
        """
        self.log('DEBUG', message, *args)

    def info(self, message, *args):
        """
        Add info log item.
        """
        self.log('INFO', message, *args)

    def warn(self, message, *args):
        """
        Add warning log item.
        """
        self.log('WARNING', message, *args)

    warning = warn

    def error(self, message, *args):
        """
        Add error log item.
        """
        self.log('ERROR', message, *args)

    def get_logs(self):
        """
        Return all logs.
        """
        return self.logs
