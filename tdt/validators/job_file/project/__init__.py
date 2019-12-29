##
# Map each project_* action to a specific class which generates the correct schema for that action
from voluptuous import Required, Schema, All, Length

action_validator_map = {
    # creating a project isn't as complicated as filtering, but does support a few additional options for
    #   color/favorite and parent/child relationships
    'create': 'Create',

    # Deleting a Project supports fewer filters/options compared to creation
    'delete': 'Delete',

}

# The schema that all project_** actions will be validated against!
base_schema = {
    # User can specify multiple labels, but they must be strings!
    Required('projects'): Schema(list, All(str, Length(min=1)), extra=False)
}
