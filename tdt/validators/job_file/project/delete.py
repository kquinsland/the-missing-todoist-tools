from voluptuous import Required, Length, Optional, Any, Range, All, Exclusive, PREVENT_EXTRA, Schema

from tdt.validators import SchemaCheck
from tdt.validators.job_file.core import filter_regex_options_schema
from tdt.validators.job_file.filter_validator import FilterValidator
# Deleting a project can be done by filter or id
from tdt.validators.job_file.project import base_schema

# Debugging
from prettyprinter import pprint as pp


_delete_obj = {

    # User is REQUIRED to indicate from where the project name is derived
    # User can create a project either by ID *or* from a search
    Required('from'): {
        # When using an ID, we just need an positive whole number
        Exclusive('id', 'project.name.source'): All(int, Range(min=1)),

        # When using filter(s) as the source of the project(s) name, validation is a bit more complex.
        # So for now, we just make sure that only name or filters is provided and if filters is provided
        #   that the user has given us a list of at least one object. Later, we'll validate each object
        ##
        Exclusive('filters', 'project.name.source'): All(list, Length(min=1)),

    }
}

# It makes no sense to have the mutate/delete option nor does it make sense to have the absent option so we
#   use a modified version of the core.__init__ one
##
_projects_filter_obj_schema = {
    Required('name'): {Required('match'): Any(str, Length(min=1))}
}


class Delete(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

        # project deletion can be specified by... project filters :)
        self.selector_schema = {
            'projects': Schema(Required(_projects_filter_obj_schema), extra=PREVENT_EXTRA),

            # User can adjust how the regex engine works
            'regex_options': Optional(filter_regex_options_schema, default=[])
        }

    def validate(self, action_block: dict):
        """
        Validates a given project_create action_block
        :param action_block:
        :return:
        """
        self.log.debug("Validating...{}".format(action_block))
        _action = action_block['action']
        _name = action_block['name']

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

        # If nothing blew up, then the high-level schema is valid. We now need to validate each of the 'from' blocks.
        ##
        self.log.debug("Validating {} 'from' objects".format(len(action_block['projects'])))
        _idx = 0
        _valid_from_blocks = []
        for o in action_block['projects']:
            _loc = "{}.from#{}".format(self.location, _idx)
            # Validate high level keys of o
            from_block = SchemaCheck(o, Schema(_delete_obj), _loc).result()

            # For now, we silently drop the from:ID
            if 'id' in from_block['from']:
                # If ID, we just assume it's valid for now. Voluptuous will have made sure that it's
                #   a positive whole number which is good enough for now. Later, we'll actually try to get
                #   the object that this ID points to
                ##
                from_block['from']['id'] = from_block['from']['id']

            # If there's a filter obj, we'll validate that now
            if 'filters' in from_block['from']:
                self.log.debug("Validating filter block on from#{}".format(_idx))
                from_block['from']['filters'] = self._validate_filters(from_block['from']['filters'])

            _valid_from_blocks.append(from_block)

            _idx += 1

        # We've validated/coerced everything, return :)
        action_block['projects'] = _valid_from_blocks
        return action_block
