from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.core import project_filter_obj_schema, filter_regex_options_schema,\
    relative_date_strings, relative_date_directions, iso_8601_fmt, option_schema_default, option_schema


from voluptuous import Required, Length, Optional, Any, Range, Boolean, All, Exclusive, PREVENT_EXTRA, Schema, In, \
    IsFile

from tdt.validators import SchemaCheck
from tdt.validators.job_file.filter_validator import FilterValidator

from tdt.defaults.colors import colors

# Debugging
from prettyprinter import pprint as pp

# Creating a label supports a few options... more complex than Basic, but nowhere near as elaborate as Filtered!
_create_obj = {

    # User is REQUIRED to indicate from where we'll name the project(s)
    # User can create a project either by name *or* from a search (currently, only filter results)
    Required('from'): {
        # When using a simple name, we just need a string
        Exclusive('name', 'project.name.source'): Any(str, Length(min=1)),

        # When using filter(s) as the source of the project(s) name, validation is a bit more complex.
        # So for now, we just make sure that only name or filters is provided and if filters is provided
        #   that the user has given us a list of at least one object. Later, we'll validate each object
        ##
        Exclusive('filters', 'project.name.source'): All(list, Length(min=1)),

    },

    # Must be between 30 and 40 or one of a fwe strings
    # See: https://developer.todoist.com/sync/v8/#colors
    # See: https://github.com/VoIlAlex/todoist-colors
    Optional('color', default=None): Any(
        In(
            list(colors.values())+list(colors.keys())
        ), None),

    # User can specify the parent project by either the name or the explicit ID
    # We default to a parent project ID of `null` to indicate a root level project
    # See: https://developer.todoist.com/sync/v8/?python#add-a-project
    Optional('parent', default={'id': 'null'}): {

        # Parent name MUSt be a string
        Exclusive('project', 'parent.selector'): str,

        # User can specify a relative date + optional direction
        # Todoist uses integers for entities that the API knows about and UUIDs for
        #   entities managed solely by the local SDK. It's hard to validate input
        #   when all you know is that valid input is a large number
        ##
        Exclusive('id', 'parent.selector'): Any('null', All(int, Range(min=0))),
    },

    # The order of all projects under parent.
    # I don't know if there's actually a limit... but it would be weird if negative
    #   numbers worked here
    ##
    # Default to NONE to indicate that the user did not specify
    Optional('child_order', default=None): Any(None, All(int, Range(min=0))),

    # Should the project been made a favorite?
    Optional('favorite', default=False): Boolean(),

    # Do we 'seed' the project we created?
    Optional('template'): {
        Required('file'): IsFile()
    }

}

# Creating a label requires at LEAST one create_object
_high_level_schema = {
    # Filters must be a list w/ at least 1 item
    Required('projects'): All([_create_obj], Length(min=1))
}

# If the date: value is present, either the match: or absent: filter can be present
_project_create_task_filter_obj_schema = {
    # Search for regex matches against task-title
    Exclusive('content', 'task:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1)),
        Optional('option', default=option_schema_default): option_schema
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
        }),

    }

}

# When a user filters on label component, the schema needs to look like this
##
# Label filters either match on a regex string *or* have an _explicit_ absent boolean flag
_project_create_label_filter_obj_schema = {
    Exclusive('name', 'label:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1)),
        Optional('option', default=option_schema_default): option_schema
    },
    Exclusive('absent', 'label:'): Boolean()

}


class Create(FilterValidator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

    def validate(self, action_block: dict):
        """
        Validates a given label_create action_block
        :param action_block:
        :return:
        """
        self.log.debug("... will validate:\n{}".format(action_block))
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
        self._schema = self._schema.extend(_high_level_schema, extra=PREVENT_EXTRA)

        # Do high level validation and store the validated (so far...) action block
        action_block = SchemaCheck(action_block, self._schema, self.location).result()

        # If nothing blew up, then the high-level schema is valid. We now need to check if any of the project(s)
        #   specify filters as their name source
        ##
        self.log.debug("...valid! Building schema for filters...")
        # TODO: the objects below are a TON of code-duplication... i need to make use of .update() so that i can
        #   programmatically  build up a schema
        self.selector_schema = {
            # Project Creation supports *additional* options not in the 'standard' schemas
            'task': Schema(Required(_project_create_task_filter_obj_schema), extra=PREVENT_EXTRA),
            'labels': Required(_project_create_label_filter_obj_schema),

            # For projects we use the 'standard' schema
            'projects': Required(project_filter_obj_schema),

            # User can adjust how the regex engine works
            'regex_options': Optional(filter_regex_options_schema, default=[])
        }

        self.log.debug("...checking {} projects for from.filters...".format(len(action_block['projects'])))
        for p in action_block['projects']:
            if 'filters' in p['from']:
                # Call out to _validate_filters. If no exception raised, then filter(s) are valid and we
                #   store the parsed/coerced/valid object
                p['from']['filters'] = self._validate_filters(p['from']['filters'])

        # We've validated/coerced everything, return :)
        return action_block
