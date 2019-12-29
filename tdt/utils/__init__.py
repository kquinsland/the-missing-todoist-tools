###
# General utilities used all throughout tdt

import logging


from tdt import exceptions
UTIL_LOGGER = logging.getLogger(__name__)


def read_file(file=str):
    """
    Reads the file
    :param file: string containing the file path
    :return:
    """
    UTIL_LOGGER.debug("Attempting to open file:{}".format(file))

    if file is not str:
        try:
            with open(file, 'r') as handle:
                return handle.read()
        except IOError:
            _e = "Unable to access or read file:{}".format(file)
            UTIL_LOGGER.fatal(_e)
            raise exceptions.FileError(_e)

    else:
        _e = "invalid file provided! Got file:`{}`".format(file)
        UTIL_LOGGER.fatal(_e)
        raise exceptions.FileError(_e)
