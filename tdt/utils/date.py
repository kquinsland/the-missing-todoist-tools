"""
    Collection of functions useful for woorking w/ Tasks and their associated Due objects
"""

# Fabulous date/time parser tool
from datetime import timedelta, datetime, date

import dateutil.parser

# So we can localize things properly
import todoist
from pytz import timezone

# Logging
import logging

# Debugging
from prettyprinter import pprint as pp

# Maps string day of week to number
_dow_map = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}

# The 'special' strings for relative date
relative_date_strings = ['now', 'today', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                         'saturday', 'sunday']


# Needs to be in format: '2020-06-28T16:00:00'
todoist_datetime_format = '%Y-%m-%dT%H:%M:%S'
todoist_date_format = '%Y-%m-%d'


def get_todoist_formatted_string_from_datetime(dt: datetime.date):
    """
    Returns a todoist API accepted string encoding for a given date/date-time
    :param dt:
    :return:
    """
    logging.debug("ALIVE. got:{}".format(dt))
    if isinstance(dt, datetime):
        logging.debug("Formatting {} with {}".format(dt, todoist_datetime_format))
        return dt.strftime(todoist_datetime_format)

    if isinstance(dt, date):
        logging.debug("Formatting {} with {}".format(dt, todoist_date_format))
        return dt.strftime(todoist_date_format)


def get_tz_aware_task_due_date(task: todoist.api.models.Item, assumed_tz: timezone('UTC')):
    """
    Todoist supports tasks with and without timezones. If the task has no time zone, the client gets to pick which
        zone should be used. Easy!

    If the task has a timezone, then Todoist will store the time zone separate from the UTC due date.
    So the 'due' object looks like:

        'due': {
            'date': '2020-01-02T15:50:00Z',  # Note, date is ALWAYS ZULU even if the task _has_ a TZ!
            'is_recurring': True, # or False
            'lang': 'en',
            'string': 'every 1 days at 07:50',
            'timezone': 'America/Los_Angeles'
            },

    So we parse the date, telling dateutil to IGNORE the timezone as we'll add that later.
    This gets us a datetime object that has the correct y/m/d h/m/s but no time zone.
    We'll apply either our assumed zone or the one explicitly declared in the task


    :param assumed_tz: The timezone that we're to 'assume' that a task takes place in. This should be the user's local
        tz.
    :param task:
    :return:
    """

    # Some tasks have No due date, return None to indicate this
    if task['due'] is None:
        return None

    ##
    # Parse the task due date, ignoring any timezone that may be present as we'll have to attach our own, later
    _dd = dateutil.parser.parse(task['due']['date'], ignoretz=True)

    # To make this function a bit more generic, we support passing in a full task object OR just a due object from
    #   something else in the todoist ecosystem... like a reminder.
    ##
    _name = task['content'] if 'content' in task else "NONE"

    # And if the task has a time zone associated with it, apply that to the ZULU we just parsed
    if 'timezone' in task['due']:
        if task['due']['timezone'] is not None:
            logging.debug("task:`{}` has a timezone:`{}` for due.date:{}"
                          .format(_name, task['due']['timezone'], task['due']['date']))

            _task_tz = timezone(task['due']['timezone'])
            _dd = _task_tz.localize(_dd)

    # Task has no time zone, so localize it to the user's local zone
    else:
        logging.debug("task://{} has no timezone, will assume '{}'...".format(_name, assumed_tz))
        _dd = assumed_tz.localize(_dd)

    return _dd


def get_dow_by_string(dow: str):
    """
    Takes a day of week as a string (e.g. "monday") and returns the pythonic weekday integer
    :param dow:
    :return:
    """

    if dow not in _dow_map.keys():
        logging.getLogger(__name__).error("Unable to convert {} to dow:".format(dow))
        return False
    return _dow_map[dow.lower()]


def get_dow_by_int(dow: int):
    """
    Works exactly  like _get_dow_by_string, but in reverse. Gets 0, returns "monday"
    :param self:
    :param dow:
    :return:
    """

    for _dow, _dow_int in _dow_map.items():
        if _dow_int == dow:
            return _dow

    # Indicate error...
    return False


def get_simplified_due_from_obj(action_block: dict):
    """
    Helper function to parse a user provided date object. Parses absent, literal, relative/explicit, delta
        into either, None, a string, a date/datetime object, or a timdedelta object.

    :param action_block:
    :return:
    """
    # If the block is valid then we know that we have _valid_ data. We just need to coerce it into
    #   useful formats that the later code wants.
    ##

    # turn due:absent: True to due: None
    if 'absent' in action_block['due']:
        # Don't need to check true/false here as absent: false is invalid
        return None

    # If the user gave us a literal string, pass that along
    if 'literal' in action_block['due']:
        return action_block['due']['literal']

    # If a user gave an explicit date/time, then all we need to do is direct assign it as voluptuous
    #   will have already done the parse
    ##
    if 'explicit' in action_block['due']:
        # We want to hide the explicit/relative.to
        _x = action_block['due'].pop('explicit')
        return _x['to']

    if 'relative' in action_block['due']:
        ##
        # The 'relative' way of specifying a date is powerful, but requires different behavior based on config
        #
        # If the user used 'now' as the relative, then voluptuous will make sure we get a datetime object.
        # If only a day of week was specified, then we'll get back only a date object.
        #
        # If we have a datetime, then the 'meaning' of before/after changes from ± 1 day to ± 1 minute.
        #
        # E.G.: Before 'monday' would be 'sunday' but before today, 11:35:15.21332434 would be today, 11:34:00
        ##
        # We want to hide the explicit/relative from later code, pop off
        _x = action_block['due'].pop('relative')

        # Find out the ref time and direction that user gave
        _ref = _x['to']
        _dir = _x['direction']

        # The time_delta object we'll use to shift to before/after
        _td = None
        if _dir == 'before':
            if isinstance(_ref, datetime):
                _td = timedelta(minutes=-1)
            else:
                # In the even of a date object, _ref will already be the 'at midnight' version, so all we need to do
                # is add or subtract one full day to get the 'before' or 'after' from _ref
                ##
                _td = timedelta(days=-1)
        else:
            # Same logic, just positive integers this time
            if isinstance(_ref, datetime):
                _td = timedelta(minutes=1)
            else:
                _td = timedelta(days=1)

        # Move forward/backwards by one unit of time (day or min)
        _ref = _ref + _td
        return _ref

    if 'delta' in action_block['due']:
        ##
        # User has given us a delta. We need to turn this into a timedetla object
        _x = action_block['due'].pop('delta')

        # Because we require the user to use the same names as the timedelta object wants, we can just take advantage
        #   of kwargs :)
        ##
        return timedelta(**_x)


# TODO: need to add timezone support. when should default to the TIMEZONE
#   that's in the user config file!
def get_next_date_by_relative(dow: str, when: date = datetime.now().date()):
    """
    """
    log = logging.getLogger(__name__)

    # We check if the caller has given us a 'special' dow
    if dow == 'today':
        return when
    elif dow == 'tomorrow':
        # TODO: in the future, it may be possible to extend this to support something like +/-x where X is the days +/-
        #   from now. for now, though, just support today/tomorrow
        ##
        _td = timedelta(days=1)
        return when + _td

    # Otherwise indicate we could not do the needful
    return False


def get_next_date_by_dow(dow: str, when: date = datetime.now().date(), direction: str = 'next'):
    """
    Takes a date object and determines when the next $dow is.
    E.G.: 2020-01-02 is a Thursday. The next Monday would be on 2020-01-06

    :param dow: The string representation of the next day of the week
    :param when: the 'when' relative to which the next dow is calculated
    :param direction: the 'direction' to search. Next or Previous
    :return:
    """
    log = logging.getLogger(__name__)

    # Check if the user has supplied a special 'relative' string like 'tomorrow'
    _relative = get_next_date_by_relative(dow, when)
    if _relative is not False:
        return _relative

    # Function does not care about H:m:s ... only date
    if isinstance(when, datetime):
        log.debug("Truncating when: {}....".format(when))
        when = when.date()
        log.debug("... to: {}".format(when))

    # No relative, so try to do the usual weekday stuff
    log.debug("attempting to figure out the '{}' dow://{} relative to `{}`".format(direction, dow, when))
    # Figure out how many days from now are are needed to get to the next/previous dow
    # Note:  Monday == 0 ... Sunday == 6.
    if direction == 'next':
        _delta = ((get_dow_by_string(dow) + when.weekday()) % 7) + 1
        log.debug("_delta to '{}' '{}' is {} ".format(direction, dow, _delta))

        # Now that we know how many days to add, make a time delta obj and add that to when
        return when + timedelta(days=_delta)

    if direction == 'previous':
        _delta = ((when.weekday() - get_dow_by_string(dow)) % 7)
        # Now that we know how many days to add, make a time delta obj and add that to when
        return when - timedelta(days=_delta)
