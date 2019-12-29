###
# The collection of actions that can be taken on "project" resources


# Inherit from...
import copy

from tdt.actions.utils import get_relevant_tasks, delete_component_by_ids, get_components_by_name_with_strings
from tdt.actions.action import Action

# Debugging
from prettyprinter import pprint as pp


class ProjectAction(Action):

    def __init__(self):
        """
        ProjectAction is base for all the Project* things. Wraps SUPER() and holds all properties common to Project* actions
        """
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("ProjectAction")

        # The component that this class will do work on
        self._component = 'projects'

        # The action that will bee taken on the component
        self._action = None

        # The actual backing store for the components the user gives us
        ##
        # List of raw Project objects user gives us
        self._component_objs = {}

        # List of components from user mapped to their IDs
        self._component_ids = {}

        # The selector(s) that we support the 'mutation' option on for $component name origination mapped
        #   to the todoist component name we'll mutate
        self._originating_mutation_selectors = {
            # We only support task title (aka content) for project name
            'task': 'content'
        }

        # Like with mutation, but the selectors that we support deletion on.
        self._originating_deletion_selectors = {
            # We support deleting tasks that originated via task, label, project selectors
            'task': 'content',
            'labels': 'name',
            'projects': 'name'
        }

        # Where we keep track of which originating components we'll delete
        self._originating_components_to_delete = {}

        # Maps the $thing/item/component to delete with the function to do the deletion
        self._originating_deletion_functions = {
            # We support deleting the task, label, project that originated the task that named the created project
            'task': '_delete_tasks_by_ids',
            'labels': '_delete_labels_by_ids',
            'projects': '_delete_projects_by_ids',
        }

    @Action.components.setter
    def components(self, value: list):
        """
        The user will supply a list of Project objects which represent Projects (and, possibly, their associated
            properties) that they want the action performed by do_work to operate on.

        To make life easier down-stream, we do a bit of processing on the object now:

            - We attempt to get the numerical ID for each string and store it along w/ the Project.
            - Sort out
        :return:
        """
        # Iterate through each object checking for an explicit name or a search we must perform to build the list of
        #   names
        ##
        self.log.debug("inspecting {} {} for explicit or dynamic names...".format(len(value), self.component))
        for o in value:
            # The user will either give us an explicit name for the project to create or will expect us to name the
            #   project(s) to be created based off of filters. In the case of a filter object, we must expand out
            #   the list of projects to create based on the task(s) that we get back from the filters
            ##
            # Check if simple case of explicit name
            if 'name' in o['from']:
                # Beyond this point, the from object is not important, only the name
                _component_name = o.pop('from')['name']

                # just store the additional settings for the project to create
                self._component_objs[_component_name] = o
                continue
            else:
                # Process any filters on the component object, respecting thee relevant mutate/delete options
                self._get_component_names_by_filters(o)

        # At this point in time, we have a complete list of all names to use for $component creation
        #   as well as the settings to use for creation in a dict indexed by the mutated (if opted) name.
        #
        # We also know which component IDs to delete after making the project!
        ##
        if len(self.components) < 1:
            # Somehow... we're called, but not going to perform any project creation!
            #   an error. Caller can figure out what they want to do w/ False.
            _e = "Somehow, no {} to create. Bail!".format(self.component)
            self.log.error(_e)
            return

        self.log.debug("Checking to see how many of the {} {} to create already exist ..."
                       .format(len(self.components), self.component))

        _existing_components = get_components_by_name_with_strings(self.api_client, self.component,
                                                                   list(self.components.keys()))

        #  Otherwise, we should have something we can store :)
        self._component_ids = {_x['name']: _x['id'] for _x in _existing_components}

    @property
    def component_ids(self):
        """
        Retruns the project -> id dict
        :return:
        """
        if self._component_ids is None:
            self.log.warning("{} accessed before set!".format('_component_ids'))
        return self._component_ids

    def _get_component_names_by_filters(self, component_obj: dict):
        """
        Helper/util function to parse out $component names from filter(s)
        :param component_obj:
        :return:
        """
        # Get the filters from the obj
        _filters = component_obj.pop('from')['filters']
        self.log.debug("Expanding {} filters into '{}' name(s)...".format(len(_filters), self.component))

        # Get the tasks that match the filters
        _originating_tasks, _source_selectors = get_relevant_tasks(self.api_client, _filters, self._assumed_tz)
        if len(_originating_tasks) < 1:
            # Emit a warning if no tasks came back
            _w = "Got back no _originating_tasks matching the {} filters. Can't create project from nothing!" \
                .format(len(_originating_tasks))
            self.log.warning(_w)

        # Otherwise, we got back some tasks. We'll use them to build the name(s) of the projects
        self.log.debug("...got back {} _originating_tasks...".format(len(_originating_tasks)))
        for _task in _originating_tasks:
            # Now that we have the task(s) to use for $component $action, we must check for any delete:True
            #   in the filter options. If the remove option is present then we'll mutate the task title before
            #   storing it as the name to use when creating the $component.
            #
            # Note: we *only* support the task.title selector as that's the only thing worth mutating when
            #   creating a $component. Said differently: if label.name selector has remove:true it won't
            #   effect the name of the task which drives the name of the project
            ##
            # The name of the task is the name of the project/component we're to create.
            _component_name = _task['content']

            # Check if the $component that sourced our namesake task is something we should mutate
            self.log.debug("checking for mutations to namesake task in {} filter(s)...".format(len(_filters)))

            for _f in _filters:
                # Check if any of the selectors we support mutation/origination on are present
                for _selector, _component in self._originating_mutation_selectors.items():
                    if _selector in _f:
                        self.log.debug("...found '{}' selector for _originating_mutation_selectors in in _f:{}"
                                       .format(_selector, _f[_selector]))
                        # Because we don't want to alter the task, we make a _deep_ copy
                        _t = copy.deepcopy(_task)
                        # Do the deletion
                        self._do_mutations_by_selector(_t, [_f], _source_selectors)
                        _component_name = _t[_component]
                        self.log.debug("mutation by selector done, will use '{}' for {}' name"
                                       .format(_component_name, self.component))

            # The component name (mutated or not) is now known. Store the component to create properties
            self._component_objs[_component_name] = component_obj

            self.log.debug("checking for deletions to namesake task in {} filter(s)...".format(len(_filters)))
            for _f in _filters:
                ###
                # Additionally, we also check if the delete:True option is set for *any* of the selector's in the filter
                #   and make a note to delete the originating task after project creation.
                ##
                for _selector, _attribute in self._originating_deletion_selectors.items():
                    self.log.debug("self._originating_deletion_selectors.items():\n{}"
                                   .format(self._originating_deletion_selectors.items()))

                    if _selector in _f:
                        self.log.debug("...found '{}' selector for _originating_deletion_selectors in in _f:{}"
                                           .format(_selector, _f[_selector]))

                        # If the user has indicated that the originating $selector should be deleted, record the
                        #   task ID now so we can delete it after project creation success
                        ##
                        # In some cases, filter obj wont have options
                        if 'option' not in _f[_selector][_attribute]:
                            continue
                        # But if it does, check if the Delete option is set
                        if _f[_selector][_attribute]['option']['delete']:

                            self.log.debug("Will delete {}://{} ({}) because {}.option:delete is true"
                                           .format('task', _task['id'], _task['content'], _selector))
                            if _selector not in self._originating_components_to_delete:
                                self._originating_components_to_delete[_selector] = []
                            self._originating_components_to_delete['task'].append(_task['id'])

    def _do_originating_components_delete(self):
        """
        Called to delete the originating components
        :return:
        """
        self.log.debug("self._originating_deletion_selectors:{}".format(self._originating_deletion_selectors))
        self.log.debug("self._originating_components_to_delete:{}".format(self._originating_components_to_delete))

        for _cmp, _lst in self._originating_components_to_delete.items():

            if _cmp not in self._originating_deletion_functions:
                _e = "Don't know how to delete {}! Supported:{}" \
                    .format(_cmp, list(self._originating_deletion_functions.keys()))
                self.log.fatal(_e)
                raise Exception(_e)

            # Otherwise, we know the function name, but do we need to invoke it?
            if len(self._originating_components_to_delete[_cmp]) < 1:
                continue

            # Figure out which function to call based on the _cmp
            _del_func_name = self._originating_deletion_functions[_cmp]
            _del_func = getattr(self, _del_func_name)

            self.log.info("Will delete {ct} {cmp} using {fn}".format(ct=len(_lst), cmp=_cmp, fn=_del_func_name))
            _del_func(_lst)

        # Commit the deletions... if we did any
        if len(self._originating_components_to_delete) > 0:
            self.log.info("Committing changes after {} deletions...".format(self._originating_components_to_delete))
            return self._commit_changes()
        else:
            return None

    def _delete_tasks_by_ids(self, task_ids: [int]):
        self._emit_event('originating_tasks_delete', task_ids)
        delete_component_by_ids(self.api_client, 'items', task_ids)

    def _delete_labels_by_ids(self, label_ids: [int]):
        self._emit_event('originating_labels_delete', label_ids)
        delete_component_by_ids(self.api_client, 'labels', label_ids)

    def _delete_projects_by_ids(self, project_ids: [int]):
        self._emit_event('originating_project_delete', project_ids)
        delete_component_by_ids(self.api_client, 'projects', project_ids)
