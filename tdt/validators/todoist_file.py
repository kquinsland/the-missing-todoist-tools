###
# Simple bit of validation for the todoist config file
###

from voluptuous import Length, Schema, Required, Any, In

import pytz

from tdt.validators import SchemaCheck

# Debugging
from prettyprinter import pprint as pp


def get_valid_todoist_schema():
    """
    Helper function to return a skeleton schema for valid actions.
    :return:
    """

    # It's a  super simple schema, a nested dict that looks like this:
    #   object['todoist']['api']['token'] = 'api_token_here'
    #  and we know that the  API token will be 40 characters, alphanumeric
    return Schema(
        {
            Required('todoist'): {
                Required('api'): {
                    Required('token'): Length(min=40, max=40, msg='Invalid Todoist API Token. Must be string with {}'
                                                                  ' characters!'.format(40))
                }
            },
            Required('client'): {
                Required('timezone'): Any(In(pytz.all_timezones))
            }
        }
    )


def validate_todoist_file(data):
    """
    Is fed the raw parsed YAML and will either blow up or return the validated yaml

    :arg data: The configuration dictionary
    :rtype: dict
    """
    return SchemaCheck(data, get_valid_todoist_schema(), 'TMTDT Config File').result()
