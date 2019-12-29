from tdt.utils.date import get_simplified_due_from_obj
from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.core import project_filter_obj_schema, filter_regex_options_schema, \
    relative_date_strings, relative_date_directions, iso_8601_fmt

from voluptuous import Required, Length, Optional, All, Exclusive, PREVENT_EXTRA, Schema, In

from tdt.validators import SchemaCheck
from tdt.validators.job_file.filter_validator import FilterValidator
from tdt.validators.job_file.task import base_schema

# Debugging
from prettyprinter import pprint as pp

# Reschedule is basically the same as delete... every structure is the same *except* for the _due_ object
from tdt.validators.job_file.task.delete import _task_delete_task_filter_obj_schema, \
    _task_delete_label_filter_obj_schema

_task_reschedule_delta_obj = {
    # When a user wants to apply a delta to the object we support everything a python timedelta supports
    #   down to the minute. It makes no real sense to have a delta of a few seconds supported.
    ##
    # Python timedelta does not support months/years, so neither do we! User must supply a whole number
    #   in either positive or negative direction
    ##
    Optional('days', default=0): int,
    Optional('hours', default=0): int,
    Optional('minutes', default=0): int,

}


_task_reschedule_due_schema = {

    # Either:
    #   - date is relative
    #   - date is explicit
    #   - date is literal
    #   - date is specified as a delta (e.g. +1 day +2h...)
    #   - date is ABSENT
    ##
    # If the user provides a literal string, then ToDoist will try to parse the string
    Exclusive('literal', 'task.due'): All(str, Length(min=1)),

    # Relative dates
    Exclusive('relative', 'task.due'): {
        # must be in _relative_date_strings and something that can be parsed into a _dt obj
        Required('to', msg="Must be one of {}".format(relative_date_strings)):
            All(In(relative_date_strings), validate_date_match),

        # Relative implies a direction
        Optional('direction', default=relative_date_directions[0],
                 msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)
    },

    # Explicit dates
    Exclusive('explicit', 'task.due:'): {

        Required('to', msg="Must be a timestamp in the format of {}".format(['Y-M-D', iso_8601_fmt])):
            validate_date_match,

        Optional('direction', default=relative_date_directions[0],
                 msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)
    },

    # Explicit dates
    Exclusive('delta', 'task.due:'): Required(_task_reschedule_delta_obj),

    # Only support True as this group is exclusive
    Exclusive('absent', 'task.due'): True

}

##
# reschedule base is normal base + a 'due' key which must be a valid date
_reschedule_base_schema = {
    Required('due'): _task_reschedule_due_schema
}
_reschedule_base_schema.update(base_schema)


class Reschedule(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()
        self.selector_schema = {
            # Task Deletion does not support the standard options for each selector in selector_schema
            'task': Schema(Required(_task_delete_task_filter_obj_schema), extra=PREVENT_EXTRA),
            'labels': Required(_task_delete_label_filter_obj_schema),

            # For projects we use the 'standard' schema
            'project': Required(project_filter_obj_schema),

            # User can adjust how the regex engine works
            'regex_options': Optional(filter_regex_options_schema, default=[])
        }

    def validate(self, action_block: dict):
        """
        Validates a given task_create block
        :param action_block:
        :return:
        """
        self.log.debug("Validating...{}".format(action_block))
        self.action = action_block['action']
        self.name = action_block['name']

        # Voluptuous can indicate 'where' the error was, but it relies on the caller (us) passing that info in
        # So we generate a simple location 'slug' based on the action and the user given name
        ##
        # Use the action/name to generate a location 'root'
        self.location = 'job://{1} (type:{0})'.format(self.action, self.name)

        # We start with making sure that we have the high level keys required for project_* actions
        # If there are any extra high-level keys, make noise
        self.log.debug("Checking high level keys...")
        self._schema = self._schema.extend(_reschedule_base_schema, extra=PREVENT_EXTRA)

        # Do high level validation and store the validated (so far...) action block
        action_block = SchemaCheck(action_block, self._schema, self.location).result()

        # If nothing blew up, then the high-level schema is valid. We now need to validate the filters
        ##
        self.log.debug("...Valid! Now validating {} filters from '{}'...".format(len(action_block['items']),
                                                                                 self.action))
        self.log.debug("checking {} 'from' block(s)'...".format(len(action_block['items'])))

        _valid_sources = []
        for obj in action_block['items']:
            # pp(obj)
            # exit()
            # Each obj will be a dict w/ only one key: from. Unwrap the from to get either filters or "ID"
            if 'id' in obj['from']:
                self.log.debug("Assuming that id:{} is valid...".format(obj['from']['id']))
                _valid_sources.append(obj['from'])
            else:
                _valid_sources.extend(self._validate_filters([obj['from']]))

        action_block['items'] = _valid_sources

        # And last, we validate the 'due'
        self.log.debug("Validating 'due'...")
        action_block['due'] = get_simplified_due_from_obj(action_block)

        # We've validated/coerced everything, return :)
        return action_block
