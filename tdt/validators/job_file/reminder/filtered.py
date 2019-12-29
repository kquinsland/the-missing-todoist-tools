###
# Validates a reminder_* action where the action supports filter/selectors
from tdt.utils.date import relative_date_strings
from tdt.validators import SchemaCheck, iso_8601_fmt
from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.filter_validator import FilterValidator
from tdt.validators.job_file.reminder import base_schema

from tdt.validators.job_file.core import filter_regex_options_schema, mutate_only_option_schema_default, \
    mutate_only_option_schema, relative_date_directions

from voluptuous import Schema, Required, Optional, Any, Length, In, ALLOW_EXTRA, PREVENT_EXTRA, Range, Datetime, \
    Exclusive, All

# Debugging
from prettyprinter import pprint as pp


# See: https://developer.todoist.com/sync/v8/?python#add-a-reminder
# 'email', 'mobile' for mobile text message or 'push' for mobile push notification.
_reminder_services = ['push', 'mobile', 'email', 'default']

# Todoist API uses `on_enter` and `on_leave` for triggers
_reminder_triggers = ['on_enter', 'on_leave']


# Location based reminders are geographic chordate bounding boxes with a human friendly name
_location_reminder_schema = {

    # There must be a WHERE object
    Required('where'): {
        # Must be a string w/ at least one character
        Required('name'): Any(str, Length(min=1)),

        # Must be a lat/long pair
        # Note, there's a lot of other info that can be properly encoded in a lat/lon pair, but
        #   the todoist API does not use any of that... so all we need to do is make sure that the
        #   user has provided two integers and that they are within the correct ranges:
        #
        #       The latitude must be a number between -90 and 90
        #       The longitude must be a number between -180 and 180.
        ##
        Required('latitude'): Any(float, Range(min=-90, max=90)),
        Required('longitude'): Any(float, Range(min=-180, max=180)),

        # We have a central point, but now we need to define a radius to define our bounding box
        # The radius is any integer that is > 0. We Default to 10 meter circle
        Optional('radius', default=10, msg="radius must be a positive whole number of meters"): Any(int, Range(min=0)),

        # Now that we have our bounding box defined, we now set the trigger. Ingress or egress?
        Optional('trigger', default=_reminder_triggers[0]): In(_reminder_triggers,
                                                               msg="Location based reminder can be trigger on ONE OF {}".format(
                                                                   _reminder_triggers))

    }

}

# Todoist also supports an absolute date/time reminder which is just a full date&timestamp
_absolute_reminder_schema = {

    # There must be a WHEN object which must be _iso_8601_fmt
    Required('when'): Datetime(format=iso_8601_fmt)

}

# Users can set an arbitrary number of minutes from 'now' to fire a reminder off with
_relative_reminder_schema = {
    # TODO: in the future, it might be possible to add support for calculating a relative offset. E.G.: remind me 15min
    #   after $other_task_due or some fixed time in the future
    # TODO: it may also be nice to implement some code to allow the users to specify an offset in hours or days and
    #   calculate the minute_offset for them.
    ##
    # for now, we ONLY support an arbitrary number of minutes from now()!
    # minutes from now must be a positive integer!
    Required('minutes'): Range(min=1)
}

# Each reminder object MUST have a type that indicates how to validate the rest of the object
# The reminder type MAPS to the schema
_reminder_types = {
    'relative': _relative_reminder_schema,
    'absolute': _absolute_reminder_schema,
    'location': _location_reminder_schema
}

# Because we'll be extending this schema, we'll want to set the `ALLOW_EXTRA` flag
_reminder_base_schema = Schema({
    # Every reminder object must have a type which we'll use for further validation
    Required('type'): In(_reminder_types, msg="reminder type must be one of {}".format(_reminder_types.keys())),

    # Additionally, each reminder object must define how the reminder is to be sent to the user
    Required('service'): In(_reminder_services, msg="reminder service must be one of {}".format(_reminder_services)),

}, extra=ALLOW_EXTRA)


##
# It makes NO SENSE to support the option:delete on source selectors. Why would you delete the thing you want
#   to put a reminder on!? Because we can't use the normal schemas from core.__init__, we create our own here
_reminder_apply_task_filter_obj_schema = {
    # Search for regex matches against task-title
    Exclusive('content', 'task:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1)),
        Optional('option', default=mutate_only_option_schema_default): mutate_only_option_schema
    },

    # Date is a bit more complicated. The user can either specify an absolute date/time stamp in ISO format
    #   or use one of a few 'relative' words like 'tomorrow' or 'monday' as well as specifying the direction
    #   of search.
    Exclusive('date', 'task:'): {

        # User wants tasks with NO DUE DATE
        # Note: Because of Exclusive() calls, it makes no sense too have
        #   absent: False, so we only accept True values
        Exclusive('absent', 'task.selector:'): True,

        # User can specify a relative date + optional direction
        Exclusive('relative', 'task.selector:'): Schema({
            Required('to', msg="Must be one of {}".format(relative_date_strings)):
            # must be in _relative_date_strings and something that can be parsed into a _dt obj
                All(In(relative_date_strings), validate_date_match),

            Optional('direction', default=relative_date_directions[0],
                     msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)

        }),

        Exclusive('explicit', 'task.selector:'): Schema({

            Required('to', msg="Must be a timestamp in the format of {}".format(['Y-M-D', iso_8601_fmt])):
                validate_date_match,

            Optional('direction', default=relative_date_directions[0],
                     msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)
        }),

    }

}

# When a user filters on label component, the schema needs to look like this
##
# Label filters either match on a regex string *or* have an _explicit_ absent boolean flag
_reminder_apply_label_filter_obj_schema = {
    Exclusive('name', 'label:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1)),
        Optional('option', default=mutate_only_option_schema_default): mutate_only_option_schema
    },
    # Can't have absent: False *and* the Exclusive() block
    Exclusive('absent', 'label:'): True

}


class Filtered(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

        self.selector_schema = {
            # Task Deletion does not support the standard options for each selector in selector_schema
            'task': Schema(Required(_reminder_apply_task_filter_obj_schema), extra=PREVENT_EXTRA),
            'labels': Required(_reminder_apply_label_filter_obj_schema),

            # User can adjust how the regex engine works
            'regex_options': Optional(filter_regex_options_schema, default=[])
        }

    def validate(self, action_block: dict):
        """
        Validates a given action_block against schema for label_* actions that support filters
        :param action_block:
        :return:
        """
        self.log.debug("Validating...{}".format(action_block))
        # Store the action and the user-given name
        self.action = action_block['action']
        self.name = action_block['name']

        # Use the action/name to generate a location 'root'
        self.location = 'job://{1} (type:{0})'.format(self.action, self.name)

        ##
        # Voluptuous does not easily encode complex conditional logic in it's schemas, so we must take a new approach
        #   here. Rather than just make one massive schema, we need to walk the dict bit by bit, pausing at the
        #   necessary level to do the validation and conditional checks.
        ##
        # We start with making sure that we have the two required keys for reminder_* actions:
        #   the reminder(s) to work on and the filters to find the correct tasks
        ##
        # Add the high level schema to existing schema and test....
        self.log.debug("Checking high level keys...")
        # If there are any extra high-level keys, make noise
        self._schema = self._schema.extend(base_schema, extra=PREVENT_EXTRA)

        # Do high level validation and store the validated (so far...) action block
        action_block = SchemaCheck(action_block, self._schema, self.location).result()

        # If nothing blew up, then the high-level schema is valid. We now need to validate the filters
        ##
        self.log.debug("...Valid! Now validating {} filters from '{}'...".format(len(action_block['filters']),
                                                                                 self.action))

        action_block['filters'] = self._validate_filters(action_block['filters'])

        # If nothing blew up, then we're now in a position to start validating the individual reminder objects
        self.log.debug("...Valid! Now validating {} reminder objects...".format(len(action_block['reminders'])))

        # After we validate / coerce each reminder object, we need to save what we have back to the action_block
        action_block['reminders'] = self._validate_reminders(action_block)

        # We've validated/coerced everything, return :)
        return action_block

    def _validate_reminders(self, action_block):
        """
        Inspects each reminder object and validates it. All validated objects are returned
        :return:
        """
        # Keep track of which obj we're validating
        _idx = 0

        # We'll store the validated objects here
        _validated_reminders = []
        for _rem in action_block['reminders']:
            # Add the index to the location
            _loc = "{}.reminder#{}".format(self.location, _idx)

            # Make sure that the reminder object confirms to _reminder_base_schema
            # If the validation passes, _rem will be the parsed/coerced/validated version of the _rem we started with :)
            _rem = SchemaCheck(_rem, _reminder_base_schema, _loc).result()

            # If nothing blew up, then we know _rem complies with _reminder_base_schema and we can now
            #   look up the TYPE of reminder and finish validation
            ##
            # Use the type of reminder to get the schema object that we should use
            _schema = _reminder_types[_rem['type']]
            # Add the validated/coerced reminder or blow up trying :)
            _validated_reminders.append(SchemaCheck(_rem,
                                                    _reminder_base_schema.extend(_schema,
                                                                                 extra=PREVENT_EXTRA),
                                                    _loc).result())
            # Increase idx for location string
            _idx += 1

        return _validated_reminders
