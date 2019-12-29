"""Logging Stuff"""
import logging

# For logging to stdout
import sys


class LogInfo(object):
    """
    small class to massage user given log settings into the global logger config
    """
    def __init__(self, cfg=dict):
        """
        Sets up logging
        :param cfg: a dict containing a few log options
        """

        # Quick sanity check on cfg; if the caller didn't give us anything, act like they gave us an empty something
        if cfg is None:
            cfg = {}

        # Get a log object
        log = logging.getLogger(__name__)

        # Default to INFO level if user didn't specify
        cfg['log_level'] = 'INFO' if 'log_level' not in cfg else cfg['log_level']

        # Use the LOG_FORMAT
        cfg['log_format'] = 'default' if 'log_format' not in cfg else cfg['log_format']

        # turn the user provided STRING back into a numerical log level
        self.numeric_log_level = getattr(logging, cfg['log_level'].upper(), None)

        # and confirm that we actually got the right thing back!
        if not isinstance(self.numeric_log_level, int):
            raise ValueError('Invalid log level: {0}'.format(cfg['loglevel']))

        # Configure logging w/ a stream handler, either a file or console out
        self.handler = logging.StreamHandler(
            open(cfg['log_file'], 'a') if cfg['log_file'] else sys.stdout
        )

        # Then figure out what log format to use. Default to a simple format:
        # Time - File - Level - Message
        self.format_string = '%(asctime)s: %(filename)s [%(levelname)-9s] %(message)s'

        # Unless we're in debug mode:
        # Time (Level) [File Function Line]  Message
        if self.numeric_log_level == logging.DEBUG:
            self.format_string = (
                '%(asctime)s (%(levelname)-5s) [%(filename)s %(funcName)15s:%(lineno)-4d]: %(message)s'
            )

        # And now that we've figured out where we log, and what level we log at, set the format
        self.handler.setFormatter(logging.Formatter(self.format_string))
        logging.root.addHandler(self.handler)
        logging.root.setLevel(self.numeric_log_level)
