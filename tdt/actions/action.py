###
# The "base" action class
###


# Debugging
from prettyprinter import pprint as pp

import logging

import todoist

from tdt import TDTException

# So we can localize things properly
from pytz import timezone


class Action(object):
    """
    The base class that every TDT action will inherit from
    """

    def __init__(self):
        # We set up a single logger in the base class
        self.log = logging.getLogger(__name__)

        ###
        # To be as efficient as possible, we make instantiating the todoist client the caller's responsibility.
        # This way, every action will use whichever client that the caller passes to us. This almost guarantees that
        #   every action will *not* result in a new client being spun up.
        ##
        self._api_client = None

        # Backup action requires the token for downloading files
        self._api_token = None

        # Todoist supports floating timezones, which means that we will encounter date/time objects that are not
        #   properly configured with a time zone. When encountering ambiguous date/time, we must assume a timezone
        # The user must configure the client with the the time zone to assume that the ambiguous objects live in
        ##
        # Store the client params for later use... if needed
        self._client_config = None

        self._assumed_tz = None

        # Action params and the  things  parsed  from them
        ##
        # the raw action_params straight from the user
        self._action_params = None

        # Each action_block is made up of a component and an action.
        # The component that this class will do work on
        ##
        self._component = None

        # The action that will bee taken on the component
        self._action = None

        # The parsed and validated objects (of type $component) that the user wants us to $action on
        self._component_objs = None

        # It's not yet fully implemented, but the idea behind every action is that it will broadcast
        #   the change(s) made to an event bus for other software to hook into
        ##
        # We also store the full options block for possible future use
        self._options = None
        self._emit_events = None

        # The --dry-run flag is passed in via the user args
        ##
        # We also store the full args for possible future use
        self._args = None
        self._dry_run = None

        ##
        # Almost all $component.$actions support filtering based on some source.selectors
        # Within that, some selectors support mutation and deletion
        ##
        # The list of tasks ids that each selector 'caught'
        self._source_selectors = {}

        # map selector -> function to mutate (remove) the matching element from task/item
        self._item_mutators = {}

        # Filters is the collection of source.selectors
        self._filters = None

    # the API client
    @property
    def api_client(self):
        if self._api_client is None:
            self.log.warning("{} accessed before set. Probably not good!".format('api_client'))
        return self._api_client

    @api_client.setter
    def api_client(self, value):
        """
        Sets the API client
        :param value:
        :return:
        """
        self._api_client = value

    # the API token
    @property
    def api_token(self):
        if self._api_token is None:
            self.log.warning("{} accessed before set. Probably not good!".format('api_token'))
        return self._api_token

    @api_token.setter
    def api_token(self, value):
        """
        Sets the API token for the few actions that need it
        :param value:
        :return:
        """
        self._api_token = value

    @property
    def client_config(self):
        if self._client_config is None:
            self.log.warning("{} accessed before set. Probably not good!".format('client_config'))
        return self._client_config

    @client_config.setter
    def client_config(self, value):
        """
        Attempts to validate and parse the client_params
        :param value:
        :return:
        """

        # Store the full data structure should we need it later...
        self._client_config = value

        # As of now, the client config is really only used to keep track of the client's preferred timezone, but
        #   will likely be expanded for other configuration items
        ##
        if 'client' not in value:
            return

        self._assumed_tz = timezone(value['client']['timezone']) if 'timezone' in value['client'] else None

    @property
    def cli_args(self):
        if self._args is None:
            self.log.warning("{} accessed before set. Probably not good!".format('cli_args'))
        return self._args

    @cli_args.setter
    def cli_args(self, value):
        """
        Attempts to validate and parse the command line args
        :param value:
        :return:
        """
        # We store the full everything that we were given should a child need it
        self._args = value

        # Parse out the useful things from args; namely dry_run
        self._dry_run = value.dry_run

    @property
    def action_params(self):
        if self._action_params is None:
            self.log.warning("{} accessed before set. Probably not good!".format('_action_params'))
        return self._action_params

    @action_params.setter
    def action_params(self, value):
        """
        Attempts to validate and parse the action params
        :param value:
        :return:
        """
        # If there are options for the action, pull them out as well
        self.options = value['options'] if 'options' in value else None

        # And ofc, store the full data structure for possible future use
        self._action_params = value

    @property
    def options(self):
        if self._options is None:
            self.log.warning("{} accessed before set. Probably not good!".format('options'))
        return self._options

    @options.setter
    def options(self, value):
        # Store everything we were given so children can process any sub-class options
        self._options = value

        if self._options is not None:
            # But now is a good time to parse out any root-level options, if we have any options @ all...
            self._emit_events = value['emit_events'] if 'emit_events' in value else None

    @property
    def dry_run(self):
        if self._dry_run is None:
            self.log.warning("{} accessed before set. Probably not good!".format('_dry_run'))
        return self._dry_run

    @property
    def filters(self):
        if self._filters is None:
            self.log.warning("{} accessed before set. Probably not good!".format('_filters'))
        return self._filters

    @property
    def action(self):
        if self._action is None:
            self.log.warning("{} accessed before set!".format('_action'))
        return self._action

    @action.setter
    def action(self, value):
        self._action = value

    @property
    def component(self):
        """
        The name of the component that class works on (task, projects, labels...etc)
        :return:
        """
        if self._component is None:
            self.log.warning("{} accessed before set!".format('_component'))
        return self._component

    @component.setter
    def component(self, value):
        self._component = value

    @property
    def components(self):
        """
        Projects is the human friendly list
        :return:
        """
        if self._component_objs is None:
            self.log.warning("{} accessed before set!".format('_component_objs'))
        return self._component_objs

    def _commit_changes(self, do_sync: bool = False):
        """
        Small wrapper function around the todoist API commit() call
        :param do_sync: Bool. Set to True if a sync() should be performed before we return
        :return:
        """
        if self.dry_run:
            self.log.info("🟡 Would have committed changes but --dry-run:`{}` prevents us from going further!"
                          .format(self.dry_run))
            return

        # Otherwise, no dry run!
        try:
            result = self.api_client.commit()

            if result is None:
                self.log.info("todoist confirmed nothing changed / nothing to .commit()")
            else:
                # the ToDoist API client 'hides' the HTTP codes except for when there's an error
                _code = result['http_code'] if 'http_code' in result else None
                if _code is not None:
                    _error_code = result['error_code'] if 'error_code' in result else None
                    _error_tag = result['error_tag'] if 'error_tag' in result else None
                    _error = result['error'] if 'error' in result else None

                    _e = "🛑 Something went wrong! {etag}: {estr}. http:{hcode} _error_code:{ecode}"\
                        .format(etag=_error_tag, estr=_error, hcode=_code, ecode=_error_code)
                    self.log.error(_e)
                    return False

            if do_sync:
                self.api_client.sync()

            # If nothing blew up...
            return True

        except todoist.api.SyncError as e:
            # e will look like:
            #   ('bde4e43e-2ddf-11ea-80ae-acde48001122', {'error_tag': 'INVALID_DATE', 'error_code': 480,
            #   'http_code': 400, 'error_extra': {}, 'error': 'Date is invalid'})
            _e = "Error saving changes to ToDoist! What went wrong:`{}`".format(e)
            self.log.error(_e)
            raise TDTException(_e)

    def _do_mutations_by_selector(self, t: todoist.api.models.Item, filters: list, selectors: list):
        """
        Removes the matching portion of the property from the task.
        :return:
        """
        # When we called out to get_relevant_tasks, we got two things back:
        #   - the list of tasks
        #   - a list of all task_ids indexed by the selector that caused the task to be included
        #       in the results :)
        #
        # For each 'filter' block that the user provided in the job file, we'll have a corresponding block in
        #   source_selectors. We go through each source-selector block, checking for the task_id in the list of
        #   tasks that each source_selector 'originated'.
        #
        # If we find the task_id in a given selectors' list, we dispatch the correct function to modify the task
        #   object as needed.
        ##
        _f = self.filters if filters is None else filters
        _s = self._source_selectors if selectors is None else selectors
        self.log.debug("There are {} filters and {} source selectors...".format(len(_f), len(_s)))

        # Keep track of the selector block we're on
        _sb_idx = 0
        for _selector_block in _s:
            self.log.debug("_selector_block:{}".format(_selector_block))

            # Iterate through each selector that we support in the current selector_block
            for _selector in self._item_mutators.keys():
                self.log.debug("_selector:{}".format(_selector))

                # Check if the task is in the list of tasks from this selector
                if t['id'] in _selector_block[_selector]:
                    # Last thing before we can actually change the task: find out how!
                    # To do this, we split the selector on `.` and that will tell us
                    #   which 'component' of the task and which 'property' matched
                    #   with the current task.
                    #
                    # E.G.: Lets say you have a _selector with the value of 'label.name' and a _filter_block that
                    #   looks like this:
                    #
                    #     {
                    #         'label': {
                    #             'name': {
                    #                 'match': 'at_HL',
                    #                 'option': {'remove': True}
                    #             }
                    #         },
                    #         'regex_options': []
                    #     }
                    #
                    # We would split the selector into component: label and property:name which would then map to
                    #   _filter_block['label']['name']. We can then check that the ['option']['remove'] is set.
                    #
                    # If it is, we then look up which function to use for removing label.name and diispatch!
                    ##
                    # We found the current task ID! Now, figure out which selector from the filter block
                    #   we need
                    # selector -> component, property
                    _x = _selector.split(".")
                    _component = _x[0]
                    _property = _x[1]

                    # Get the component, property out of filter block
                    ##
                    # full filter object needed by functions we'll call in a moment
                    _filter_obj = _f[_sb_idx]

                    # Get the individual selector out, if it's present
                    # In some cases (labels) the filter block will look like {'absent': True}
                    #   and we won't be able to get the labels.name
                    ##
                    if _property not in _filter_obj[_component]:
                        self.log.debug("_filter_obj[{cmp}]: {got} Expected:{exp}"
                                       .format(cmp=_component, exp=_property, got=_filter_obj[_component]))
                        continue
                    _f = _filter_obj[_component][_property]

                    self.log.debug("task://{tid} ({tname}) because '{selector}' = '{match}'...".format(
                        tid=t['id'],
                        tname=t['content'],
                        selector=_selector,
                        match=_f['match']
                    ))

                    # Check if user wants us to remove, bail if no.
                    if not _f['option']['mutate']:
                        self.log.debug("... NOT removing matching token")
                        continue

                    # User does want us to remove from task
                    if _selector not in self._item_mutators:
                        _e = "Don't know how to mutate item by {}. PANIC!".format(_selector)
                        self.log.fatal(_e)
                        raise Exception(_e)

                    # Figure out which function to call based on the reminder type
                    _mutator_name = self._item_mutators[_selector]
                    _mutator = getattr(self, _mutator_name)
                    self.log.debug("Mutating task by {} with with _mutator_name:{}".format(_selector, _mutator_name))
                    _mutator(t, _filter_obj)

            # Move on to the next source block
            _sb_idx += 1

        return

    def _emit_event(self, *args, **kwargs):
        """
        Hook function designed to emit events / signal to other software when an item has been modified.
        Not yet implemented!
        :return:
        """
        # The idea is to hook here to mqtt event bus so other things are aware of what just happened
        #pp(kwargs)
        #pp(args)
        self.log.debug('emit_event {} not yet implemented'.format(self._emit_events))
