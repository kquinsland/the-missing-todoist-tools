"""
Creates Tasks
"""
from tdt.actions.utils import get_components_by_name_with_strings

# Debugging
from prettyprinter import pprint as pp

from tdt.actions.task import TaskAction


class TaskCreateAction(TaskAction):

    def __init__(self):
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("TaskCreateAction!")
        self.action = 'create'

        # When a user gives us strings for a given property, we'll need to resolve the string(s) into a numerical ID
        ##
        self._property_name_to_id_map = {
            'project': [],
            'parent_task': [],
            'section': [],

            'labels': []
        }

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
        for _component_name, _component_obj in self.components.items():

            # There are three different 'properties' that a user can set via ID or by String.
            # We check for any string(s) and resolve them to IDs.
            ##
            self._reset_property_name_to_id_map()
            self._resolve_strings_to_ids(_component_obj)

            # Coerce the user-provided date into a format that todoist API will work with
            ##
            # Temp remove. I need to play w/ the API to see what the minimum viable due object is
            _component_obj['due'] = self._parse_date(_component_obj['due'])

            self.log.debug("due has been coerced to:{}".format(_component_obj['due']))

            ##
            # We have resolved each of the user-provided properties into IDs, but we have not validated if the IDs are
            #   permitted! If the user says "make $task under $parent_task in $project.$section" but $section is not
            #   in $project or $parent_task is not in $project, then we can't continue!
            #
            ##
            self.log.debug("Validating/ Disambiguating resolved IDs...")
            self._validate_resolved_ids()

            # Merge the resolved IDs into the _component_obj
            _component_obj.update(self._property_name_to_id_map)

            # Now that all the (known) strings are resolved to IDs, we can create the task!
            self.log.debug("{} {}://{} with properties:{}".format(self.action, self.component, _component_name,
                                                                  _component_obj))

            _kwa = {
                # content / title of the task
                'content': _component_name,

                'due': _component_obj['due'],

                # Parent project ID, or 'null'
                'project_id': self._property_name_to_id_map['project'],
                # Priority int
                'priority': _component_obj['priority'],
                # List of integer labels
                'labels': _component_obj['labels'],

                # The ID of the parent task, if any
                'parent_id': self._property_name_to_id_map['parent_task'],

                'child_order': _component_obj['child_order'],

                'section_id': self._property_name_to_id_map['section'],

                'day_order': _component_obj['day_order'],

                # This is one of those weird ones that needs to be a 1 or 0, not Bool like 'auto_reminder'
                'collapsed': int(_component_obj['collapsed']),

                'auto_reminder': _component_obj['auto_reminder'],
                'auto_parse_labels': _component_obj['auto_parse_labels']

            }
            self.log.debug("_kwa :{}".format(_kwa))
            _r = self.api_client.items.add(**_kwa)

            self._emit_event('task_create', _r)

        # After adding all the $components, commit changes.
        return self._commit_changes()

    @TaskAction.components.setter
    def components(self, value: list):
        """
        The user will supply a list of Task objects which represent Tasks to do $action on

        As task_create does not support filters, we don't bother doing anything significant here
        """
        # We pull out the 'name' (called content) and use that as the key to the rest of the properties
        for o in value:
            _component_name = o.pop('content')
            self._component_objs[_component_name] = o

        ##
        # TODO: it would be nice to have a 'dont-create-duplicate-tasks' flag that would walk each object in
        #   self.components to see if there is an existing task by the same content and parent project  (and labels,
        #   child_order ... etc)
        #
        # The code to do this will be a PITA as it'll mean resolving each (label, parent_project, parent_task)
        #   string to an ID and then looking through every task under the parent project for an identical name
        #   if the name matches, then check the rest of the properties...
        ##

    def _resolve_strings_to_ids(self, component_obj: dict):
        """
        Resolves strings into IDs
        :param component_obj:
        :return:
        """

        for prop in self._property_name_to_id_map:

            # User did not specify the optional, use todoist default
            if component_obj[prop] is None:
                self.log.debug("will use default for {} for {}.{}".format(self.action, self.component, prop))
                continue

            # Otherwise, check if the user specified an ID to use
            if 'id' in component_obj[prop]:
                self.log.debug("will use ids for {} for {}.{}".format(self.action, self.component, prop))
                # Caller has just given us IDs so use those directly
                self._property_name_to_id_map[prop] = [component_obj[prop]['id']]
                continue

            # Last, check if the user wants us to resolve strings to ids
            if 'name' in component_obj[prop]:
                # Ok, the user has specified a $prop by name. We must now resolve that into an ID
                ##
                self.log.debug("Will need to fetch IDs for {}://{}".format(prop, component_obj[prop]['name']))

                # Which property will we fetch?
                ##
                # Note: We do need to do a little bit of mapping between the fields that the user
                #   will provide and what get_components_by_name_with_strings wants. This is not ideal, but
                #   it saves the user from confusion when they have to enter ONLY ONE STRING for
                #   a field called 'projects'.
                ##
                _p = prop
                if prop == 'project':
                    _p = 'projects'

                if prop == 'section':
                    _p = 'sections'

                # we must map parent_task to 'items' for the call to get_component_by_names
                if prop == 'parent_task':
                    _p = 'items'

                # the queries that we pass in will be exactly the name(s) that the user gave us
                if prop == 'labels':
                    _q = component_obj[prop]['name']
                else:
                    # when user specifies a string for parent project or task, we get only one string,
                    #   so that string needs to be put in a list before we hand off. It's the difference
                    #   between looking for a Project called 'Inbox' and 5 projects known as [I,n,b,o,x]
                    ##
                    _q = [component_obj[prop]['name']]

                _things = get_components_by_name_with_strings(self.api_client, _p, _q)

                # We'll get back the full result set, but only care about the IDs
                self._property_name_to_id_map[prop] = [_t['id'] for _t in _things]

    def _validate_resolved_ids(self):
        """
        :return:
        """

        """
        There are three properties that the user can give to us as a string that _can_ have multiple matches.
          parent_task
          parent_project
          section

        Because we _only_ support mentions by string, it is impossible to *always* know the precise entity that
          the user is referring to. A user can have three different projects, all called 'Inbox' in the root of their
          account. They'll all have distinct IDs, but the string name alone is not enough to ID them. The user would
          have to *also* tell us the color, favorite, position/order... etc so we could uniquely ID the entity.

        In some cases, it *may* be possible to use other 'clues' to narrow down which of multiple IDs the user may
            have meant. E.G.: If there are two projects, both called 'Inbox' but only one of them as the section called
            'some-unique-section-name' then we may be able to infer that the user meant the id that maps to the project
            called Inbox with the section 'some-unique-section-name'.
            
        However, this is a non-trivial bit of code to write that - as my initial efforts show - is error prone and can't
            reliably eliminate 100% of the ambiguous cases. I have decided to toss the buggy code and just emit a fatal
            error to the user which informs them of the ambiguous situation and invites them to refer to the specific
            duplicate property by an explicit ID
             
        """
        for _prop, ids in self._property_name_to_id_map.items():
            self.log.debug("checking for more than one ID for _prop:{}. ids:{}".format(_prop, ids))
            if len(ids) > 1:
                _e = "Ambiguous Situation! A total of {ct} {prop} has been resolved, however, " \
                     "only *one* {prop} is supported for {comp}.{act}! Please specify the {prop} by explicit ID! " \
                     "Got:{ids}".format(ct=len(ids), prop=_prop, comp=self.component, act=self.action, ids=ids)
                self.log.fatal(_e)
                raise ValueError(_e)

        # At this point, we'll either have blown up @ one of the ambiguous cases, OR we'll have managed to make sure
        #   that each 'property' in the self._property_name_to_id_map has either 0 or 1 IDs.
        #   (except for labels... that is the only property that supports more than one ID!)
        #
        # Up to now, it was helpful to keep things in a list format but now it's time to turn the properties
        #   with lists of at most one ID into just the ID and properties with no ID into the 'default' value that the
        #   API wants us to use when submitting our request
        ##
        for _key, _list in self._property_name_to_id_map.items():
            # Labels is the only property that can have more than one
            if _key == 'labels':
                continue

            if len(_list) == 1:
                self.log.debug("condense _key:{} into single".format(_key))
                self._property_name_to_id_map[_key] = _list.pop(0)
            else:
                # ToDoist API uses the string 'null' for properties not set... Except for the project
                _v = 'null'
                if _key in ['project']:
                    _v = None
                self._property_name_to_id_map[_key] = _v

        self.log.debug("Managed to condense self._property_name_to_id_map to: {}".format(self._property_name_to_id_map))

    def _reset_property_name_to_id_map(self):
        self._property_name_to_id_map = {
            'project': [],
            'parent_task': [],
            'section': [],
            'labels': []
        }
