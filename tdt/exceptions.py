"""ToDoist Tools Exceptions"""


class TDTException(Exception):
    """
    Everything that's not a Python or ToDoist Exception will stem from here :)
    """


class ConfigurationError(TDTException):
    """
    Exception raised when an invalid job file is detected
    """


class FileError(TDTException):
    """
    Exception raised when a file can't be accessed
    """


class JobFileError(TDTException):
    """
    Exception raised when a Job File contains invalid YAML
    """


class TodoistFileError(TDTException):
    """
    Exception raised when a Job File contains invalid YAML
    """


class TodoistClientError(TDTException):
    """
    Exception raised when Something happened w/ the ToDoist client
    """
