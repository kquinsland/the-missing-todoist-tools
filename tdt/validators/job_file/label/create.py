from voluptuous import Required, Length, Optional, Boolean, All, PREVENT_EXTRA, Schema

from tdt.validators import SchemaCheck
from tdt.validators.job_file.label import base_schema
from tdt.validators.job_file.validator import Validator

from tdt.defaults.colors import colors

# Debugging
from prettyprinter import pprint as pp


def _validate_color(value):
    """
    We need to make sure that the user chosen color exists and map it to the correct integer value or just
    verify that the user provided integer is valid
    :param value:
    :return:
    """
    if value in colors.values():
        return value

    if value in colors.keys():
        return colors[value]

    _e = "Did not get a valid color!"
    raise ValueError(_e)


# Creating a label supports a few options... more complex than Basic, but nowhere near as elaborate as Filtered!
_create_obj = {

    #Each label object MUST have at a MINIMUM the a string called 'label'
    Required('label'): All(str, Length(min=1)),

    # Must be between 30 and 40 or one of a fwe strings
    # See: https://developer.todoist.com/sync/v8/#colors
    # See: https://github.com/VoIlAlex/todoist-colors
    Optional('color', msg="Color must be either the NAME or numerical Value"): _validate_color,
    Optional('favorite'): Boolean()

}


class Create(Validator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

    def validate(self, action_block: dict):
        """
        Validates a given label_create action_block
        :param action_block:
        :return:
        """
        ###
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

        # If nothing blew up, then the high-level schema is valid. We now need to check each of the
        #   labels.
        ##
        self.log.debug("... Valid! Checking {} labels ...".format(len(action_block['labels'])))
        _valid_components = []
        _idx = 0
        for _l in action_block['labels']:
            _loc = "{}.label#{}".format(self.location, _idx)
            _valid_components.append(SchemaCheck(_l, Schema(_create_obj), _loc).result())
            _idx += 1

        # Return all the valid label objects
        action_block['labels'] = _valid_components
        return action_block
