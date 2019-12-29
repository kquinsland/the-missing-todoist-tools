"""
Reschedules Tasks
"""
from datetime import timedelta

from tdt.actions.utils import get_component_by_ids, get_relevant_tasks

# Debugging
from prettyprinter import pprint as pp

from tdt.actions.task import TaskAction
from tdt.utils.date import get_tz_aware_task_due_date, get_todoist_formatted_string_from_datetime


class TaskRescheduleAction(TaskAction):

    def __init__(self):
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.action = 'reschedule'

        # The list of resolved task IDs that we'll reschedule to the due date
        self._component_ids = []

        # The due date/time that tasks will be rescheduled to
        self.due = None

    def do_work(self, action_params: dict):
        """
        Does the work of TaskRescheduleAction
        :param action_params:
        :return:
        """

        # Store the things that the user has asked us to reschedule
        self.components = action_params[self.component]
        # And the date/time they want them rescheduled to
        self.due = self._parse_date(action_params['due'])

        if len(self._component_ids) < 1:
            self.log.warning("No tasks to reschedule.")
            return

        self.log.info("♻️ 📆 Will {act} '{ct}' {cmp}".format(act=self.action, ct=len(self._component_ids),
                                                             cmp=self.component))

        # Iterate through each of the user-given objects and perform additional validation and resource resolution as
        #   needed.
        ##
        # fetch the task for each of the user / resolved IDs
        _tasks = get_component_by_ids(self.api_client, self.component, self._component_ids)
        for t in _tasks:
            # If the user gave us a timedelta object, then they want to postpone the task. It is impossible
            #   for a task w/ no explicit due date to be postponed by any length of time so we skip them :)
            ##
            if isinstance(self.due, timedelta):
                if t['due'] is None:
                    _w = "⚠️ Will not postpone {}://{} ({}) because it's has no due date!"\
                        .format(self.component, t['id'], t['content'])
                    self.log.warning(_w)
                    continue
                else:
                    # Figure out when the task is due
                    _task_due = get_tz_aware_task_due_date(t, self._assumed_tz)
                    # Add the offset
                    _task_due = _task_due + self.due
                    # We need to turn the adjusted into a new due{} object
                    self.due = {'date': get_todoist_formatted_string_from_datetime(_task_due)}

            # Now that all the (known) strings are resolved to IDs, we can create the task!
            self.log.debug("{} {}://{} ({}) to: {}".format(self.action, self.component, t['id'], t['content'],
                                                           self.due))
            t.update(due=self.due)

        self._emit_event('{}_{}'.format(self.component, self.action))
        return self._commit_changes()

    @TaskAction.components.setter
    def components(self, value: list):
        """
        User will supply a list of 'sources' which will either be an ID or some sort of filter.
        If id, then all we need to do is verify that it exists
        If filter(s) then we resolve them to IDs.
        """
        # Check for any IDs
        for obj in value:
            if 'id' in obj:
                self.log.debug("Validating {}://...".format(self.component, obj['id']))
                _cmp = get_component_by_ids(self.api_client, self.component, [obj['id']])
                # If we didn't get _one_ component back, emit a warning and move on. If we did get ONE back then
                #   we can be very occident that it exists in the users account and is therefore able to be deleted.
                ##
                if len(_cmp) != 1:
                    self.log.debug("... Invalid!")
                    _w = "⚠️ Was not able to confirm existence of {}://{}! Will not {} it!"\
                        .format(self.component, obj['id'], self.action)
                    self.log.warning(_w)
                    continue
                else:
                    self.log.debug("... Valid! Will {} {}://{}".format(self.action, self.component, obj['id']))
                    self._component_ids.append(obj['id'])
            else:
                self.log.debug("Parsing {} from filter...".format(self.component))
                _items, _ = get_relevant_tasks(self.api_client, [obj], self._assumed_tz)
                x = [_itm['id'] for _itm in _items]
                self.log.debug("... got {} ids".format(len(x)))
                self._component_ids.extend(x)
