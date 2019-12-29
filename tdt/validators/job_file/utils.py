import logging
from os import path

from voluptuous import Invalid


def _is_valid_file(value):
    """
    Wrapper function
    :param value:
    :return:
    """
    return _is_valid_filesystem_thing(value, 'file')


def _is_valid_dir(value):
    """
    Wrapper function
    :param value:
    :return:
    """
    return _is_valid_filesystem_thing(value, 'dir')


def _is_valid_filesystem_thing(value, thing=''):
    """
    Called by voluptuous to validate if the 'value' is a file or dir
    :param value:
    :param thing:
    :return:
    """
    log = logging.getLogger(__name__)
    log.info("Validating that value:{} is a:{}".format(value, thing))

    if type(value) is not str:
        _e = "Can't confirm that `{}` is a valid {}. got:{}".format(value, thing, type(value))
        log.error(_e)
        raise Invalid(_e)

    if thing == 'dir':
        if not path.isdir(value):
            _e = "Can't confirm that `{}` is a valid  {} :(".format(value, thing)
            log.error(_e)
            raise Invalid(_e)

    elif thing == 'file':
        if not path.isfile(value):
            _e = "Can't confirm that `{}` is a valid  {} :(".format(value, thing)
            log.error(_e)
            raise Invalid(_e)
    else:
        _e = "Dont know how to validate thing:{}. Got:{} :(".format(thing, value)
        log.error(_e)
        raise Invalid(_e)

    # return value if it's a valid thing
    return value


def _is_valid_date(value):
    import dateutil.parser

    try:
        dateutil.parser.parse(value)
        return value
    except dateutil.parser.parser._parser.ParserError as pe:
        _e = "Can't validate {} as a datetime. pe:{}".format(value, pe)
        log = logging.getLogger(__name__)
        log.error(_e)
        raise Invalid(_e)

