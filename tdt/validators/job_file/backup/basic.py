from voluptuous import Required, Schema, All, Length, PathExists

# Makes sure that user given string is in the PAST
from tdt.validators.job_file import _valid_past_time


# Does the validation
from tdt.validators.job_file.validator import Validator
from tdt.validators import SchemaCheck

# A backup_* filter object must have...
_filter_obj = {

    # Each filter object has a root-level object called filter which will be a dict containing...
    Required('filter'): {

        # A "when" block that is either a re
        Required('when'): _valid_past_time,
    }

}

# When validating a label_* action that supports filtering, we have additional schema to add
backup_schema = {
    # For now, we only support ONE
    Required('filters'): All([_filter_obj], Length(min=1)),

    # There's also the option of WHERE to save
    Required('options'): {
        Required('save_location'): PathExists()
    }

}


class Basic(Validator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

    def validate(self, action_block: dict):
        """
        Validates a given label_* action_block when the action only needs basic validation
        :param action_block:
        :return:
        """
        self.log.debug("Validating:\n{}".format(action_block))
        _action = action_block['action']
        _name = action_block['name']

        # Add the schema elements that are unique to label_* class of actions to the schema
        # Add filtered schema to the base schema we inherited from super()
        self._schema = self._schema.extend(backup_schema)

        # Voluptuous can indicate 'where' the error was, but it relies on the caller (us) passing that info in
        # So we generate a simple location 'slug' based on the action and the user given name
        ##
        _loc = 'job://{1}({0})'.format(_action, _name)

        # Call the schema-checker on the action block caller passed to us
        return SchemaCheck(action_block, self._schema, _loc).result()
