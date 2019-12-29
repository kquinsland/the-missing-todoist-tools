"""
Creates Projects
"""

import todoist

from tdt.actions.utils import get_component_by_ids, get_components_by_name_with_strings
from tdt.actions.mutators import remove_component_attribute_by_regex
from tdt.actions.project import ProjectAction

# Debugging
from prettyprinter import pprint as pp


class ProjectCreateAction(ProjectAction):

    def __init__(self):
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("ProjectCreateAction!")
        self.action = 'create'

        # User can specify some selectors from a filter to be the origination for project name during project creation
        # If the user has set the option:remove for the supported selector, we will use the mutator to perform the
        #   mutation on the property we copy from the originating entity
        ##
        self._item_mutators = {
            # We support removing tokens from task.title
            'task.content': '_remove_task_title_match'
        }

    def do_work(self, action_params: dict):
        """
        Does the work of ProjectCreateAction
        :param action_params:
        :return:
        """
        self.action_params = action_params

        # set projects; triggers fetch of project_ids as well as a validation measure
        self.components = action_params[self.component]



        # We'll now have a list of all the _known_ projects and their IDs. Iterate through the full list of projects
        #   that the caller gave us and find the Projects that are _missing_. Those are the ones that we'll need to
        #   create
        ##
        # Get the keys/project names we were able to find IDs for
        _existing = set(self.component_ids)
        self.log.debug("{}:\n{}".format('_existing', _existing))

        # Subtract out the keys we have from the ones we're told to make
        _new = set(self.components) - _existing
        if len(_new) < 1:
            self.log.warning("⚠️ No difference in the {0} to create and the {0} that already exist! Action ends now!"
                             .format(self.component))
            return

        # For each $component that does not yet exist, make!
        self.log.info("ℹ️ Of the {} {} to create, {} already exist, will create {}..."
                      .format(len(self.components), self.component, len(_existing), len(_new)))

        for _component_name in _new:
            _component_obj = self.components[_component_name]
            # We need to do a bit of data type munging to comply with the todoist API
            ##

            #   if the user has specified a parent project by name, resolve that name to an ID
            ##
            _parent_id = self._get_parent_prj_id(_component_obj)

            # If None is set (default) then todoist uses a default color
            _c = _component_obj['color']

            # If None is set (default) then todoist just puts it 'next'
            _child_order = _component_obj['child_order']

            _kwa = {
                'name': _component_name,
                'color': _c,
                'parent_id': _parent_id,
                'child_order': _child_order,
                #   is_favorite needs a 1 or 0, not True, False :/
                'is_favorite': int(_component_obj['favorite'])
            }
            self.log.debug("{} {}://'{}' with _kwa:{}".format(self.action, self.component, _component_name, _kwa))
            _r = self.api_client.projects.add(**_kwa)
            self._emit_event('project_add', _r)

            # If the user wants to 'seed' the project from a template, we do so now
            if 'template' in _component_obj:
                self.log.debug("Seeding {}://'{}' with file://{}".format(self.component, _component_name,
                                                                         _component_obj['template']['file']))
                self._seed_project_with_template(_r, _component_obj['template']['file'])

        # After adding all the $components, commit changes.
        _r = self._commit_changes()

        # If it looks like the project creation worked, then issue the call to delete the originating components
        #   as needed
        return self._do_originating_components_delete()

    @staticmethod
    def _remove_task_title_match(t: todoist.api.models.Item, filter_obj: dict):
        return remove_component_attribute_by_regex(t, filter_obj, component='task', attribute='content')

    def _seed_project_with_template(self, project: todoist.api.models.Project, template_file: str):
        """
        Applies a template to a project.

        The todoist API is smart enough to use UUIDs under the hood for for changes that only exist
          locally. That is, we can get an ID for the project that's JUST been created even though we've
          not yet committed the changes to the server. We can use the temporary ID for local operations
          and once we commit() to the server, the changes will be persisted and the temporary IDs will be
          replaced with permanent IDs that the server will also understand.

        A temporary project will look like:

        Project(
            {
              'id': '$11809284-2f5f-11ea-9c61-acde48001122',
              'name': 'project-name-here',
              'parent_id': 2205676774
            }
        )

        But this behavior does NOT apply to template uploads, unfortunately. The import_into_project() call does not
            support batching. It runs IMMEDIATELY and can't work with temp UUIDs.

        So this means that we are required to commit() immediately after creating the new project. Then
            we can consult our local cache for the updated/not-temp project ID. It's not ideal, but
            as long as we're making many API requests per min, we should not hit any rate-limiting.

            See: https://github.com/Doist/todoist-python/issues/69

        :param project:
        :param template_file:
        :return:
        """
        # Force a sync w/ the server to make sure any newly created projects get actual IDs
        self._commit_changes(do_sync=True)

        # Assuming nothing was thrown, we should be OK to query the cache for the updated project ID
        _prj = get_components_by_name_with_strings(self.api_client, 'projects', [project['name']])

        if len(_prj) != 1:
            # If we couldn't get the project ID... despite having just? created it... then we certainly
            #   can't upload the template to it! Treat this as an error, but not fatal.
            _e = "Unable to obtain the project ID that template_file:`{}` should be uploaded to. " \
                 "This likely means that the project was not created. :(".format(template_file)
            self.log.error(_e)
            return False

        # Length of 1, unwrap
        _prj = _prj.pop()

        # Otherwise, let's try the upload!
        self.log.debug("Attempting to apply the template file:`{}` to the _new_prj:`{}`/({})"
                       .format(template_file, _prj['name'], _prj['id']))

        self.api_client.templates.import_into_project(_prj['id'], template_file)
        # `import_into_project` does not update the local cache... so we must do so now
        _r = self._commit_changes(do_sync=True)
        # TODO: what data too fire off?
        self._emit_event('project_seed')

        # And assuming that nothing blew up, return!
        return _r

    def _get_parent_prj_id(self, component_obj: dict):
        """
        Helper function to get the parent project ID from a component_obj of class 'project'
        :param component_obj:
        :return:
        """
        # User can specify a parent project by either the ID OR a name/filter, but if nothing is specified, then
        #   the default value that voluptuous inserts is 'null'. This is the value that todoist API expects when there
        #   is to be no parent project
        ##
        parent = component_obj.get('parent')

        if 'id' in parent and parent['id'] == 'null':
            # No parent project detected and the 'expected' default already set
            return parent['id']

        if 'id' in parent:
            # The user _has_ specified a parent project by ID, we need to verify that it exists!
            _pid = parent['id']
            self.log.debug("Determining if parent {}://{} is valid...".format(self.component, _pid))
            _components = get_component_by_ids(self.api_client, self.component, [_pid])

            if len(_components) != 1:
                # User told us to use an ID as a parent task, we can't confirm that it _is_ a parent task. ABORT!
                _e = "...Unable to determine that {}://{} is valid! Will abort!".format(self.component, _pid)
                self.log.error(_e)
                raise Exception(_e)

            # Otherwise, we were able to confirm that _pid is a real project ID!
            return _pid

        if 'project' in parent:
            # Like w/ the case of the 'naked' ID, we need to turn any string into oa project, too
            _prj = parent['project']
            self.log.debug("Determining if parent {}://{} exists...".format(self.component, _prj))
            _components = get_components_by_name_with_strings(self.api_client, self.component, [_prj])

            # If we get 0 results, it means that the project does nto *YET* exist. It may be that the user has
            #   already asked for us to create it, however.
            ##
            if len(_components) != 1:
                # User told us to use a string as a parent task, but we can't
                _e = "...Unable to determine that {}://{} exists! Ambiguous as we got {} results, need one!"\
                    .format(self.component, _prj, len(_components))
                self.log.error(_e)
                raise Exception(_e)

            # Otherwise, we were able to confirm that _prj is a real project, we return the ID that maps to _prj
            return _components[0]['id']
