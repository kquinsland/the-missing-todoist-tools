
from tdt.validators.job_file.core import  filter_regex_options_schema

from voluptuous import Required, Length, Optional, Any, PREVENT_EXTRA, Schema

from tdt.validators import SchemaCheck
from tdt.validators.job_file.filter_validator import FilterValidator
from tdt.validators.job_file.label import base_schema

# Debugging
from prettyprinter import pprint as pp


_label_filter_obj_schema = {
    Required('name'): {Required('match'): Any(str, Length(min=1))}
}


class Delete(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

        # Label deletion can be specified by... label filters :)
        self.selector_schema = {
            'labels': Schema(Required(_label_filter_obj_schema), extra=PREVENT_EXTRA),


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
        self.log.debug("...Valid! Now validating {} filters from '{}'...".format(len(action_block['labels']),
                                                                                 self.action))

        _idx = 0
        _valid_sources = []
        for obj in action_block['labels']:
            _loc = "{}.from#{}".format(self.location, _idx)
            # pp(obj)
            # exit()
            # Each obj will be a dict w/ only one key: from. Unwrap the from to get either filters or "ID"
            if 'id' in obj['from']:
                self.log.debug("Assuming that id:{} is valid...".format(obj['from']['id']))
                _valid_sources.append(obj['from'])
            else:
                self.log.debug("Validating filter block on from#{}".format(_idx))
                _valid_sources.extend(self._validate_filters([obj['from']]))

            _idx += 1

        action_block['labels'] = _valid_sources

        # We've validated/coerced everything, return :)
        pp(action_block)
        return action_block
