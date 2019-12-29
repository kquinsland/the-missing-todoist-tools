"""
Deletes Labels
"""
import re

from tdt.actions.utils import get_component_by_ids, delete_component_by_ids, get_components_by_name_with_regex,\
    parse_regex_options

# Debugging
from prettyprinter import pprint as pp

from tdt.actions.label import LabelAction


class LabelDeleteAction(LabelAction):

    def __init__(self):
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.action = 'delete'

        # The list of resolved task IDs that we'll delete
        self._component_ids = []

        # When a user gives us strings for a given property, we'll need to resolve the string(s) into a numerical ID
        ##
        self._property_name_to_id_map = {
            'project': [],
            'parent_task': [],
            'section': [],

            'labels': []
        }

    @property
    def component_ids(self):
        if self._component_ids is None:
            self.log.warning("{} accessed before set!".format('_component_ids'))
        return self._component_ids

    def do_work(self, action_params: dict):
        """
        Does the work of ProjectCreateAction
        :param action_params:
        :return:
        """

        # Store the things that the user has asked us to create
        self.components = action_params[self.component]

        # Iterate through each of the user-given objects and perform additional validation and resource resolution as
        #   needed.
        ##
        self._emit_event('{}_{}'.format(self.component, self.action))
        delete_component_by_ids(self.api_client, self.component, self._component_ids)

        # After adding all the $components, commit changes.
        return self._commit_changes()

    @LabelAction.components.setter
    def components(self, value: list):
        """
        User will supply a list of 'sources' which will either be an ID or some sort of filter.
        If id, then all we need to do is verify that it exists
        If filter(s) then we resolve them to IDs.

        """
        if not isinstance(value, list) or len(value) < 1:
            _e = "Need at least one valid {}. got:{}".format(self.component, value)
            self.log.error(_e)
            raise ValueError(_e)

        # Check for any IDs or filters
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
                self.log.info("🔎 Searching for {} matching :{}".format(self.component, obj[self.component]))

                # Pull out the labels.match into a regex query, parse the regex flags if present
                _re_flags = parse_regex_options(obj)
                _labels_title_re = re.compile(obj[self.component]['name']['match'], flags=_re_flags)

                # Run the filter to get the labels
                _items = get_components_by_name_with_regex(self.api_client, self.component, _labels_title_re)

                x = [_itm['id'] for _itm in _items]
                self.log.debug("... got {} ids".format(len(x)))
                self._component_ids.extend(x)