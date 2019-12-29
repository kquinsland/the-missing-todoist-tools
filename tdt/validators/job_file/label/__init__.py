##
# Map each label_* action to a specific class which generates the correct schema for that label_* action
from voluptuous import Required, Schema, All, Length

action_validator_map = {
    # creating a label isn't as complicated as filtering, but does support a few additional options for color/favorite
    'create': 'Create',

    # deleting a label is dead simple; nothing to validate :)
    'delete': 'Delete',

    # Applying a label *does* support filters
    'apply': 'Apply'
}

# The schema that all label_* actions will be validated against!
base_schema = {
    # User can specify multiple labels, but they must be strings!
    Required('labels'): Schema(list, All(str, Length(min=1)), extra=False)
}
