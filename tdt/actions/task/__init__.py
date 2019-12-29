###
# The collection of actions that can be taken on "task" resources
##
from tdt.actions.action import Action

from datetime import date, timedelta
from tdt.utils.date import get_todoist_formatted_string_from_datetime

# Debugging
from prettyprinter import pprint as pp


class TaskAction(Action):

    def __init__(self):
        """
        TaskAction is base for all the Task* things. Wraps SUPER() and holds all properties common to Project* actions
        """
        # Set up logging and the like
        super().__init__()

        # Note: todoist calls 'tasks' 'items'
        self.component = 'items'

        # The actual backing store for the components the user gives us
        ##
        # List of raw Tasks objects user gives us to create
        self._component_objs = {}

    @property
    def component_ids(self):
        """
        Retruns the project -> id dict
        :return:
        """
        if self._component_ids is None:
            self.log.warning("{} accessed before set!".format('_component_ids'))
        return self._component_ids

    def _parse_date(self, date_obj):
        """
        Parses the due property into actual date/time that ToDoist API can work with
        :param date_obj: The date object to parse
        :return:
        """
        ##
        # After some testing there are two possible 'formats' the due= argument can take.
        #   either:
        #       'due': None
        #   *or*
        #       'due': {
        #           'date': '2020-06-29T14:00:00',
        #           'is_recurring': True,
        #           'lang': 'en',
        #           'string': 'every day 14:00',
        #           'timezone': None
        #           },
        #   *or*
        #       a literal timedelta object
        #
        # Where ONLY the DATE *OR* STRING is _required_:
        #
        #       'due': {'date': '2020-06-28T16:00:00'}
        #       'due': {'string': 'every day 5:00pm'}
        ##

        # The object that caller should use for the due= argument
        _due = None

        # If the user wants No due date, then None will be set. This is the first of two valid formats discussed above
        if date_obj is None:
            return date_obj

        # If the user wants to postpone the task, then we just pass through as there's nothing else for us to do until
        #   we have the actual task handy
        ##
        if isinstance(date_obj, timedelta):
            return date_obj

        # If the user has specified a LITERAL string, then we just assume it's valid and pass off to ToDoist
        #   for processing
        ##

        if isinstance(date_obj, str):
            self.log.debug("crafting literal _due with :{}".format(date_obj))
            _due = {"string": date_obj}
            return _due

        # Otherwise, the user passed in something that was coerced into a datetime, now we need to format the
        #   object into a string that ToDoist will work with
        #
        # See: https://developer.todoist.com/sync/v8/?python#due-dates
        ##
        if isinstance(date_obj, date):
            _due = {'date': get_todoist_formatted_string_from_datetime(date_obj)}
            return _due

        # We we make it _this far_ then something went wrong
        _e = "Unsupported component_obj['due']. Got:{} with type:{}".format(date_obj, type(date_obj))
        raise Exception(_e)

