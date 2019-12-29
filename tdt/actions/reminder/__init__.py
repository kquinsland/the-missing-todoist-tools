###
# The collection of actions that can be taken on "reminder" resources
##


# Inherit from...
from tdt.actions.action import Action


class ReminderAction(Action):

    def __init__(self):
        """
        ReminderAction is base for all the label* things. Wraps SUPER() and holds all properties common to label* actions
        """
        # Set up logging and the like
        super().__init__()

        # Note: todoist calls 'tasks' 'items'
        self.component = 'reminders'

        # The actual backing store for the components the user gives us
        ##
        # List of raw Reminder objects user gives us to create
        self._component_objs = {}

