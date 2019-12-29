# Debugging
from prettyprinter import pprint as pp


import todoist

from tdt.actions.utils import get_relevant_tasks
from tdt.actions.label import LabelAction
from tdt.actions.mutators import remove_component_attribute_by_regex, remove_component_by_ids


class LabelApplyAction(LabelAction):

    def __init__(self):
        # Set up parents; let them validate things for us
        super().__init__()
        self.action = 'apply'

        # The list of tasks ids that each selector matched
        self._source_selectors = {}

        # map selector -> function to remove the matching element from task/item
        self._item_mutators = {
            # We support removing the label from matching tasks
            'labels.name': '_remove_label_name_match',

            # We support removing tokens from task.title
            'task.content': '_remove_task_content_match'
        }

    def do_work(self, action_params: dict):
        """
        Does the work of LabelApplyAction
        :param action_params:
        :return:
        """
        # We can assume that voluptuous has already validated the action_params so just assign to kick off
        #   the necessary parsing
        self.action_params = action_params
        # Some schemas make more sense to have in the general component: from: filters:
        #   layout, and other schemas (like reminders) are much easier to do individually
        #   with the filters in their own block and the reminders in another block
        ##
        self._filters = self.action_params['filters']

        # Pull out the label objects
        self.components = action_params[self.component]

        self.log.debug("Fetching '{}' from {} filters....".format(self.component, len(self.filters)))

        # Get the tasks that match the filters
        self.log.info("Looking for tasks to apply {} {} to....".format(len(self.filters), self.component))

        _t, _s = get_relevant_tasks(self.api_client, self.filters, self._assumed_tz)
        self._matching_tasks = _t
        self._source_selectors = _s

        if len(self._matching_tasks) < 1:
            _e = "🚨 There are no tasks that match filters:{}".format(self.filters)
            self.log.error(_e)
            return self._matching_tasks

        # Check that we were able to lookup ids for the labels previously...
        if len(self._component_ids) < 1:
            _e = "Unable to determine the label ID for labels:`{}`." \
                .format(self._component_objs)
            self.log.error(_e)
            # We don't need to blow up fatally, just indicate an error w/ this task and return False to indicate
            #   that we could not complete the job.
            return False

        # Now that we've got the relevant tasks, iterate over every task...
        self.log.info("⏳ Beginning work on {} tasks...".format(len(self._matching_tasks)))
        for t in self._matching_tasks:

            # Turn the label_ids that user wants us to add into a set
            _lbls_to_add = set(self._component_ids.values())
            self.log.debug("_lbls_to_add:{}".format(_lbls_to_add))

            # Turn the labels that the task has already into a set
            _task_lbls = set(t['labels'])
            self.log.debug("_task_lbls:{}".format(_task_lbls))

            # Let the user know what the difference is
            # Start with the labels to add and subtract out any labels the item has already
            _delta = _lbls_to_add - _task_lbls
            self.log.info("➕ Adding {} new labels to task://{} ({})".format(len(_delta), t['id'], t['content']))
            self.log.debug("_delta:{}".format(_delta))

            # the .update() call persists the changes to the _local_ cache. We'll wait until after processing the
            #   option.remove statements before we persist the changes to the server
            _all = list(_task_lbls.union(_lbls_to_add))
            self.log.debug("_all:{}".format(_all))
            t.update(labels=_all)
            self._emit_event('label_apply', t)

            # Since we're iterating through tasks, now is a good time to process any of the filter.*.option.mutate:true
            #   flags...
            ##
            self._do_mutations_by_selector(t, self.filters, self._source_selectors)

        # And at the end of our operation, we need to save our changes and persist them to the server
        self.log.info("💾 Saving changes to {} matching_tasks".format(len(self._matching_tasks)))

        return self._commit_changes()

    def _remove_label_name_match(self, t: todoist.api.models.Item, filter_obj: dict):
        return remove_component_by_ids(self.api_client, t, filter_obj, component='labels', attribute='name')

    def _remove_task_content_match(self, t: todoist.api.models.Item, filter_obj: dict):
        return remove_component_attribute_by_regex(t, filter_obj, component='task', attribute='content')
