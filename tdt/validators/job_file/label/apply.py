###
# Validates a label_* action where the action supports filter/selectors
##

# Debugging
from prettyprinter import pprint as pp

from tdt.utils.date import relative_date_strings
from tdt.validators import SchemaCheck, iso_8601_fmt
from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.core import mutate_only_option_schema_default, mutate_only_option_schema, \
    relative_date_directions, filter_regex_options_schema, project_filter_obj_schema
from tdt.validators.job_file.filter_validator import FilterValidator
from tdt.validators.job_file.label import base_schema


from voluptuous import Required, Length, All, PREVENT_EXTRA, Schema, Exclusive, Optional, Any, In

# Todoist supports two basic types of reminders: time and location.
# At a BARE MINIMUM, the caller must present two lists: one for the reminder(s) to be created
#   and one for the filters that will select out the tasks to get the reminder(s)
##
_high_level_schema = {
    # The list of labels we'll be applying
    # Label is any non-empty string
    Required('labels'): All([str], Length(min=1)),

    # The list of filters to select tasks we'll work on
    # Filter objects are a bit complicated so we'll validate them later
    Required('filters'): All(list, Length(min=1))

}


##
# It makes NO SENSE to support the option:delete on source selectors. Why would you delete the thing you want
#   to put a label on!? Because we can't use the normal schemas from core.__init__, we create our own here
_label_apply_task_filter_obj_schema = {
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
_label_apply_label_filter_obj_schema = {
    Exclusive('name', 'label:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): All(str, Length(min=1)),
        Optional('option', default=mutate_only_option_schema_default): mutate_only_option_schema
    },
    # Can't have absent: False *and* the Exclusive() block
    Exclusive('absent', 'label:'): True

}

# Label apply inherits from the base schema, adds filters
_base_schema = {
    # Like labels, at least one filter must be defined
    Required('filters'): Schema(All(list, Length(min=1)), extra=False)
}
_base_schema.update(base_schema)


class Apply(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

        self.selector_schema = {
            # Label Application supports task, labels, projects
            ##
            # We don't support deletion deletion for tasks, just mutation
            'task': Schema(Required(_label_apply_task_filter_obj_schema), extra=PREVENT_EXTRA),

            # Same with labels: mutation only
            'labels': Required(_label_apply_label_filter_obj_schema),

            # Projects are not mutable
            'projects': Required(project_filter_obj_schema),

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
        self._schema = self._schema.extend(_base_schema, extra=PREVENT_EXTRA)

        # Do high level validation and store the validated (so far...) action block
        action_block = SchemaCheck(action_block, self._schema, self.location).result()

        # If nothing blew up, then the high-level schema is valid. We now need to validate the filters
        ##
        self.log.debug("...Valid! Now validating {} filters from '{}'...".format(len(action_block['filters']),
                                                                                 self.action))

        action_block['filters'] = self._validate_filters(action_block['filters'])

        # If nothing blew up, then we're now in a position to start validating the individual reminder objects
        self.log.debug("...Valid! Now validating {} reminder objects...".format(len(action_block['filters'])))

        # We've validated/coerced everything, return :)
        return action_block
