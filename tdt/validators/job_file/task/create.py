from tdt.utils.date import get_simplified_due_from_obj
from tdt.validators.job_file import validate_date_match
from tdt.validators.job_file.core import relative_date_strings, relative_date_directions, iso_8601_fmt

from voluptuous import Required, Length, Optional, Any, Range, Boolean, All, Exclusive, PREVENT_EXTRA, Schema, In

from tdt.validators import SchemaCheck
from tdt.validators.job_file.task import base_schema

from tdt.validators.job_file.validator import Validator

# Debugging
from prettyprinter import pprint as pp

_task_create_project_schema = {
    # The name of the project to create the task under
    Exclusive('name', 'task.project'): All(str, Length(min=1)),
    # It's hard to validate beyond "must be positive whole number"
    Exclusive('id', 'task.project'): All(int, Range(min=1)),

}

# If the user does not specify which project, inbox!
_task_create_project_default = {
    'name': 'Inbox'
}

# Todoist supports three distinct date-times
# See: https://developer.todoist.com/sync/v8/?python#due-dates
##
_task_create_due_schema = {

    # Either:
    #   - date is absent
    #   - date is relative
    #   - date is explicit
    ##
    # It does not make sense to have the Exclusive block _and_ accept absent:false
    #   so we make sure that absent = true, if the user has set it :)
    ##
    Exclusive('absent', 'task.due'): True,

    # If the user provides a literal string, then ToDoist will try to parse the string
    Exclusive('literal', 'task.due'): All(str, Length(min=1)),

    # Relative dates
    Exclusive('relative', 'task.due'): {
        # must be in _relative_date_strings and something that can be parsed into a _dt obj
        Required('to', msg="Must be one of {}".format(relative_date_strings)):
            All(In(relative_date_strings), validate_date_match),

        # Relative implies a direction
        Optional('direction', default=relative_date_directions[0],
                 msg="Must be one of {}".format(relative_date_directions)): In(relative_date_directions)
    },

    # Explicit dates
    Exclusive('explicit', 'task.selector:'): {

        Required('to', msg="Must be a timestamp in the format of {}".format(['Y-M-D', iso_8601_fmt])):
            validate_date_match
    }



}

# If the user does not specify _when_ the task to be created is due, we set to None!
_task_create_due_default = {
    'absent': True
}


_task_create_parent_task_schema = {
    # The name of the parent task
    Exclusive('name', 'task.parent.task'): All(str, Length(min=1)),

    # It's hard to validate beyond "must be positive whole number"
    Exclusive('id', 'task.parent.task'): All(int, Range(min=1)),

}


_task_create_section_schema = {
    # The name of the parent task
    Exclusive('name', 'task.section'): All(str, Length(min=1)),

    # It's hard to validate beyond "must be positive whole number"
    Exclusive('id', 'task.section'): All(int, Range(min=1)),

}


_task_create_labels_schema = {
    # The name of the parent task
    Exclusive('name', 'task.labels'): All([str], Length(min=1)),

    # to validate each ID, we'd need a function similar to how i validate regex flags
    # So for now, just make sure that the user has provided a list of integers w/ at least
    #   one item
    ##
    Exclusive('ids', 'task.labels'): All([int], Length(min=1)),
}

# Creating a label supports a few options... more complex than Basic, but nowhere near as elaborate as Filtered!
_task_obj = {

    # We *require* that the content of the task be provided. Any string will do
    Required('content', msg="The task content must be a string w/  at  least one character"): All(str, Length(min=1)),

    # The Project is optional, but if specified  must conform to _task_create_project_schema
    Optional('project', msg="Either provide the name of an existing project or a project ID",
             default=None): Any(None, _task_create_project_schema),

    # Todoist supports three distinct date/time formats. If the user does not specify a due date, then the task
    #   will have "None"
    Optional('due', msg="", default=_task_create_due_default): _task_create_due_schema,


    # Tasks can have a priority as well
    Optional('priority', msg="priority must be one of {}, where {} is highest priority.".format(range(1, 4), 4),
             default=1): Range(min=1, max=4),

    # It is possible to define a parent task, this works just like parent project
    Optional('parent_task', msg="Either provide the name of an existing task or a task ID",
             # Todoist API wants the string 'null' tasks with no section. We'll use None to represent that
             #  for most of the code base, though
             default=None): Any(None,  _task_create_parent_task_schema),

    # TODO: does child_order ONLY apply when there is a parent task?
    # For now, take it no matter what,
    Optional('child_order', default=None): Any(None, Range(min=1)),

    # When viewing the 'today' or 'next 7 days' view, this field adjust the order
    #   smaller integers @ top
    ##
    Optional('day_order', default=None): Any(None, Range(min=1)),


    # Within a project, tasks can have sections, they behave just like project/parent_task
    Optional('section', msg="Either provide the name of an existing section or a section ID",
             # Todoist API wants the string 'null' tasks with no section. We'll use None to represent that
             #  for most of the code base, though
             default=None): Any(None, _task_create_section_schema),

    # If the task has children, should the children present in collapsed state?
    Optional('collapsed', default=False): Boolean(),

    # A task can be created with labels, like with parent_task, parent_project, we let the user specify strings or IDs
    # Default to no labels for the assigned task
    Optional('labels', default=[]): Any([], _task_create_labels_schema),

    # Todoist will helpfully apply a default reminder to every task
    Optional('auto_reminder', default=True): Boolean(),

    # Todoist will helpfully try too parse out @labels from the task content and auto-apply the labels
    Optional('auto_parse_labels', default=True): Boolean()
}


class Create(Validator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

    def validate(self, action_block: dict):
        """
        Validates a given task_create block
        :param action_block:
        :return:
        """
        self.log.debug("Validating...{}".format(action_block))
        self.action = action_block['action']
        self.name = action_block['name']

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

        # If nothing blew up, then the high-level schema is valid. We now need to check if any of the project(s)
        #   specify filters as their name source
        ##
        self.log.debug("...Valid! Now validating {} tasks from {}...".format(len(action_block['items']), self.action))

        _valid_tasks = []
        _idx = 0
        for t in action_block['items']:
            _loc = "{}.item#{}".format(self.location, _idx)

            # We need to do some additional validation that Voluptuous does not handle:
            #   - section can only be included if there's a non-default parent project
            ##
            _valid = SchemaCheck(t, Schema(_task_obj), _loc).result()
            # user can supply a due date in one of several different formats. Later code won't care and will
            #   only want an explicit date/datetime
            ##
            _valid['due'] = get_simplified_due_from_obj(_valid)
            _valid_tasks.append(_valid)
            _idx += 1

        # We've validated/coerced everything, return :)
        action_block['items'] = _valid_tasks
        return action_block
