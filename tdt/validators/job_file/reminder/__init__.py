##
# Map each reminder_* action to a specific class which generates the correct schema for that reminder_* action
from voluptuous import Required, Length, Any

action_validator_map = {
    # Applying a reminder requires filters
    'apply': 'Filtered'
}

# Todoist supports two basic types of reminders: time and location.
# At a BARE MINIMUM, the caller must present two lists: one for the reminder(s) to be created
#   and one for the filters that will select out the tasks to get the reminder(s)
##
base_schema = {
    # The list of reminders to apply
    Required('reminders'): Any(list, Length(min=1)),

    # The list of filters to select tasks with
    Required('filters'): Any(list, Length(min=1)),
}


