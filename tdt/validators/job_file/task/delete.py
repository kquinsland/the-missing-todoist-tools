from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.core import project_filter_obj_schema, filter_regex_options_schema, \
    relative_date_strings, relative_date_directions, iso_8601_fmt

from voluptuous import Required, Length, Optional, Any, Boolean, All, Exclusive, PREVENT_EXTRA, Schema, In

from tdt.validators import SchemaCheck
from tdt.validators.job_file.filter_validator import FilterValidator
from tdt.validators.job_file.task import base_schema

# Debugging
from prettyprinter import pprint as pp


_task_delete_task_filter_obj_schema = {
    # Search for regex matches against task-title
    Exclusive('content', 'task:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1))
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

_task_delete_label_filter_obj_schema = {
    Exclusive('name', 'label:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): All(str, Length(min=1))
    },
    Exclusive('absent', 'label:'): Boolean()

}


class Delete(FilterValidator):

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
        self._schema = self._schema.extend(base_schema, extra=PREVENT_EXTRA)

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

        # We've validated/coerced everything, return :)
        return action_block
