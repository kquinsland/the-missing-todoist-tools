"""
Default schema objects and associated lists for Filter Object validation
"""
from voluptuous import Required, Optional, Boolean, Exclusive, Any, Length, Schema, All, In

from tdt.validators import iso_8601_fmt
from tdt.validators.job_file import relative_date_strings, validate_date_match

# When a user specified relative date, they need to include a direction
relative_date_directions = ['before', 'after']

# See: https://docs.python.org/3/library/re.html#contents-of-module-re
# See: https://pythex.org/
# Short hand version of the regex flags
regex_flags = ['re.I', 're.L', 're.M', 're.S', 're.U', 're.X']


# When user can specify an option: it must look like this
option_schema = Required(
    {
        Optional('mutate', default=False): Boolean(),
        Optional('delete', default=False): Boolean()
    }
)
# When user omits a required option: object, use this
option_schema_default = {
    'mutate': False,
    'delete': False
}

##
# There are some cases where it does not make sense to support a delete: option
# When user can specify an option: it must look like this
mutate_only_option_schema = Required(
    {
        Optional('mutate', default=False): Boolean()
    }
)
# When user omits a required option: object, use this
mutate_only_option_schema_default = {
    'mutate': False
}

# When a user filters on task component, the schema needs to look like this
##
# Tasks can be selected by either the title *OR* their due date
# If the date: value is present, either the match: or absent: filter can be present
task_filter_obj_schema = {
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

            Optional('direction', default=relative_date_directions[0],
                     msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)
        }),

    }

}

# When a user filters on label component, the schema needs to look like this
##
# Label filters either match on a regex string *or* have an _explicit_ absent boolean flag
label_filter_obj_schema = {
    Exclusive('name', 'label:'): {
        # If task.title is specified, MUST be a string w/ at least 1 char
        Required('match'): Any(str, Length(min=1)),
        Optional('option', default=option_schema_default): option_schema
    },
    # Can't have absent: False *and* the Exclusive() block
    Exclusive('absent', 'label:'): True
}

# When a user filters on project component, the schema needs to look like this
project_filter_obj_schema = {
    Optional('name'): {
        # If project.name is specified, MUST be a string w/ at least 1 char
        Required('match'): All(str, Length(min=1))
    }
}


def _validate_regex(value):
    """
    Voluptuous does not (easily) support checking that _each_ value of an array is valid... so we define our own :)
    :param value:
    :return:
    """
    # When Voluptuous calls us, all we know is that value is a list
    # We then go through each item in the list and make sure that it matches the schema:
    _sch = Schema(
        In(regex_flags, msg="Must be one of {}".format(regex_flags))
    )
    for itm in value:
        # Make sure that the item is in _regex_flags.
        _sch(itm)

    # If nothing blew up, then the value that Voluptuous passed in to us is valid :)
    return value


# Regex Options Schema, very simple, must be a list and each
#   thing in the list must be a valid regex option :)
filter_regex_options_schema = _validate_regex
