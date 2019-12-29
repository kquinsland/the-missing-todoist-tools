##
# Map each task_* action to a specific class which generates the correct schema for that action
from voluptuous import Required, Schema, Length

action_validator_map = {
    # Tasks are not incredibly complex, but they do support the most options/settings for any item that the Todoist
    #   API uses. As such, there's a lot of exclusive, inclusive group/options to validate against
    'create': 'Create',

    # Task deletion is a lot like 'regular' filter -> action flow. The delete validation process is _very_ different
    #   from the validation done from creation!
    'delete': 'Delete',

    # Task rescheduling is a lot like deletion. Only deference is that instead of task.delete() we call task.update()
    #   with a new due={} object.
    ##
    'reschedule': 'Reschedule',

}

# The schema that all project_** actions will be validated against!
base_schema = {
    # at a bare minimum, there must be a key called tasks which points to a list of at least one item
    Required('items'): Schema(list, Length(min=1), extra=False)
}
