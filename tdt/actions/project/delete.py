"""
Deletes Projects from a given ToDoist account.
"""
import re

from tdt.actions.utils import parse_regex_options, get_component_by_ids, delete_component_by_ids
from tdt.actions.project import ProjectAction

from tdt.actions.utils import get_components_by_name_with_regex

# Debugging
from prettyprinter import pprint as pp


class ProjectDeleteAction(ProjectAction):

    def __init__(self):
        super().__init__()
        self.action = 'delete'

    @ProjectAction.components.setter
    def components(self, value: list):
        """
        The user can specify projects to delete in a slightly different format compared to create/apply
        Inside value['projects'] we should have a list of objects, each with a 'from' field. inside the from field
            will either be an ID or a Filters block.

            If ID, then we fetch the information behind it and store as a test of it's validity.
            If Filters, then we must run the filters to get the objects and then store them like as if we had just
                been given IDs
        :param value:
        :return:
        """
        if not isinstance(value, list) or len(value) < 1:
            _e = "Need at least one valid {}. got:{}".format(self.component, value)
            self.log.error(_e)
            raise ValueError(_e)

        for o in value:
            _from = o.pop('from')

            if 'filters' in _from:
                # User has given us some number of strings to match against
                for _filter_obj in _from['filters']:
                    self.log.debug("processing filter:{}".format(_from['filters']))

                    # Pull out the projects.match into a regex query, parse the regex flags if present
                    _re_flags = parse_regex_options(_filter_obj)
                    _projects_title_re = re.compile(_filter_obj['projects']['name']['match'], flags=_re_flags)

                    # Run the filter to get the projects
                    _projects = get_components_by_name_with_regex(self.api_client, self.component, _projects_title_re)

                    # For each project that we got, store
                    self._component_ids = {_x['name']: _x['id'] for _x in _projects}
                continue

            if 'id' in _from:
                # user gave us an ID. We now need too fetch the project object for that ID.
                _lid = _from['id']
                self.log.debug("Fetching {}://{}".format(self.component, _lid))
                _lbl = get_component_by_ids(self.api_client, self.component, [_lid])

                if len(_lbl) != 1:
                    _e = "Ambiguous search result for {}://{}. Expected _exactly_ one result, got:{}! CANT DELETE!"\
                        .format(self.component, _lid, len(_lbl))
                    self.log.warning(_e)
                    continue

                # Unwrap the 1 result
                self._component_ids = {_x['name']: _x['id'] for _x in _lbl}

    def do_work(self, action_params: dict):
        """
        Does the work of projectDeleteAction
        :param action_params:
        :return:
        """

        # set projects; triggers fetch of project_ids as well as a validation measure
        self.components = action_params[self.component]

        # We'll now have a list of all the _known_ projects and their IDs. Iterate through the full list of projects
        #   that the caller gave us and find the Projects that are _missing_. Those are the ones that we'll need to
        #   create
        ##
        # Get the keys/project names we were able to find IDs for
        _existing = set(self._component_ids)

        # Delete the component(s) that exist
        for _component_name in _existing:
            # _existing is a set of all the _names_ of existing $component. We need to get the ID that belongs to the
            #   name before we can make the delete call
            ##
            _cid = self._component_ids[_component_name]
            self._emit_event('{}_{}'.format(self.component, self.action), _cid)
            delete_component_by_ids(self.api_client, self.component, [_cid])

        # After deleting all the $components, commit changes.
        return self._commit_changes()
