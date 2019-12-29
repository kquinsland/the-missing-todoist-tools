from voluptuous import Date

import logging

from tdt.validators.job_file.utils import _is_valid_file, _is_valid_dir, _is_valid_date


from datetime import datetime, date
from tdt.utils.date import get_next_date_by_dow, relative_date_strings

from tdt.validators import iso_8601_fmt


def validate_date_match(value):
    """
    To make life much easier, we're going to do all the date:match process logic at the same time as validation.
    When setting a task.date: selector, user has two options:
        - provide a valid ISO8601 stamp, time and timezone optional
        - provide one of a few valid strings to indicate a 'relative' date. E.G.: "today, tomorrow, monday...sunday"

    :param value:
    :return:
    """
    # Check if the user supplied a relative string
    if value in relative_date_strings:
        _idx = relative_date_strings.index('now')
        if value == relative_date_strings[_idx]:
            _dt = datetime.now()
        else:
            _dt = get_next_date_by_dow(value)
        return _dt
    else:
        # If the string is not one of the few special ones, we must try to coerce it into a python datetime object using
        #   one of the supported formats
        ##
        logging.debug("NON RELATIVE STRING:{}".format(value))
        _dt = None

        # Try Y-M-D format, first
        try:
            _dt = datetime.strptime(value, Date.DEFAULT_FORMAT).date()
            logging.debug("using {}, _DT:{}".format(Date.DEFAULT_FORMAT, _dt))
            return _dt
        except ValueError as ve:
            # Simple format didn't work, try moore complicated ISO format
            _dt = datetime.strptime(value, iso_8601_fmt)
            logging.debug("SIMPLE NOT OK, _DT:{}".format(_dt))
            return _dt


def _valid_past_time(value):
    """
    Wraps validate_date_match to enforce PAST time
    :param value:
    :return:
    """

    # When is now() ?
    # TODO: pull the localization of user in here!?
    _now = datetime.now()

    # Remove invalid relative strings
    if value == 'tomorrow':
        # Remove the string 'tomorrow' from relative strings, then use for error generation
        _idx = relative_date_strings.index('tomorrow')
        relative_date_strings.pop(_idx)
        _e = "The relative date: '{}' can't be used when referring to the past! Please use one of:{}"\
            .format(value, relative_date_strings)
        raise ValueError()

    # Coerce into *a* date-time object
    _d = validate_date_match(value)

    # Check that _d is < _now()
    if _d is None:
        # Caller should not try to pass None as a date here... but if they do, we'll catch and Fail
        _e = "Can't validate that a None date occurred in the past!"
        logging.error(_e)
        raise ValueError(_e)

    # User provided something that's a date or a datetime. We now check if it's in the past or not
    if type(_d) is date:
        # We can't compare _now (datetime) to  _d (date), so we need to create a datetime object from the date and use
        #   that for a apples to apples comparison.
        ##
        _temp = datetime(_d.year, _d.month, _d.day)
        if _temp < _now:
            logging.debug("_d:{} (cast to {}) is in the past, relative to _now:{}".format(_d, _temp, _now))
            return _d
    else:
        if _d < _now:
            logging.debug("_d:{} is in the past, relative to _now:{}".format(_d, _now))
            return _d

    # If it's not in the past, we at least know that we were able to parse a DateTime from the user input
    # We simply pass the value in to this helper to get the previous date-time object
    ##
    logging.debug("_d:{} is NOT in the past, relative to _now:{}... Walking backwards...".format(_d, _now))
    _dt = get_next_date_by_dow(value, _now, direction='previous')
    return _dt

