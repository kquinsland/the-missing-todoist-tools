# Debugging
from prettyprinter import pprint as pp

from datetime import datetime, timedelta
from pytz import timezone
import dateutil
import todoist

from tdt.actions.mutators import remove_component_attribute_by_regex, remove_component_by_ids
from tdt.actions.reminder import ReminderAction
from tdt.actions.utils import get_relevant_tasks
from tdt.utils.date import get_tz_aware_task_due_date
from tdt.utils.reminders import get_reminders_by_task_id


class ReminderApplyAction(ReminderAction):

    def __init__(self):
        # Set up parents; let them validate things for us
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("ReminderApplyAction")

        # The tasks that matched the filters
        self._matching_tasks = []

        # The list of tasks ids that each selector matched
        self._source_selectors = {}

        # map reminder type to the name of the function that can build the correct type of reminder
        self._reminder_builders = {
            'location': '_set_location_reminder',
            'absolute': '_set_absolute_reminder',
            'relative': '_set_relative_reminder'
        }

        # map selector -> function to remove the matching element from task/item
        self._item_mutators = {
            # We support removing the label from matching tasks
            'labels.name': '_remove_label_name_match',

            # We support removing tokens from task.title
            'task.content': '_remove_task_title_match'
        }

    @ReminderAction.components.setter
    def components(self, value: list):
        """
        Parses each of the reminder objects from the user
        :param value:
        :return:
        """

        # Each reminder is 'indexed' by the 'type':
        #   - where
        #   - when (relative, absolute)
        ##
        if not isinstance(value, list) or len(value) < 1:
            _e = "Need at least one valid {}. got:{}".format(self.component, value)
            self.log.error(_e)
            raise ValueError(_e)

        # There's nothing fancy here that we need to do. Voluptuous has already validated everything so we
        #   just store
        ##
        self._component_objs = value

        ##
        # TODO: it would be nice to have a 'dont-create-duplicate-tasks' flag that would walk each object in
        #   self.components to see if there is an existing task by the same content and parent project  (and labels,
        #   child_order ... etc)
        #
        # The code to do this will be a PITA as it'll mean resolving each (label, parent_project, parent_task)
        #   string to an ID and then looking through every task under the parent project for an identical name
        #   if the name matches, then check the rest of the properties...
        ##

    def do_work(self, action_params: dict):
        """
        Does the work of ReminderApplyAction
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

        # Pull out the reminder objects
        self.components = action_params['reminders']

        self.log.debug("Fetching '{}' from {} filters....".format(self.component, len(self.filters)))

        # Get the tasks that match the filters
        self.log.info("🔎 Looking for tasks to apply {} reminders to....".format(len(self.filters)))

        _t, _s = get_relevant_tasks(self.api_client, self.filters, self._assumed_tz)
        self._matching_tasks = _t
        self._source_selectors = _s

        self.log.debug("...got {} tasks from {} selectors...".format(len(_t), len(_s)))
        if len(self._matching_tasks) < 1:
            _e = "⚠️ There are no tasks that match filters:{}".format(self.filters)
            self.log.error(_e)
            return self._matching_tasks

        # Now that we've got the relevant tasks, iterate over every task...
        self.log.info("⏳ Beginning work on {} tasks...".format(len(self._matching_tasks)))
        for t in self._matching_tasks:

            # Todoist does not store reminders 'with' task objects, we'll use a dedicated reminders API to manage them.
            # All we need is the task ID to work w/ the dedicated API
            ##
            for _r in self.components:
                if _r['type'] not in self._reminder_builders:
                    _e = "Don't know how to create a reminder of type {}. PANIC!".format(_r['type'])
                    self.log.fatal(_e)
                    raise Exception(_e)

                # Based on the reminder type, we call the reminder.add() API differently.
                # Each helper function also does duplicate detection and other sanity checks before
                #   creating the reminder
                ##
                # Figure out which function to call based on the reminder type
                _builder_name = self._reminder_builders[_r['type']]
                _builder = getattr(self, _builder_name)
                self.log.debug("Creating '{}' reminders with _builder_name:{}".format(_r['type'], _builder_name))
                _builder(t, _r)

            # Since we're iterating through tasks, now is a good time to process any of the filter.*.option.remove:true
            #   flags...
            self._do_mutations_by_selector(t, self.filters, self._source_selectors )

        # And at the end of our operation, we need to save our changes and persist them to the server
        self.log.info("💾 Saving changes to {} matching_tasks".format(len(self._matching_tasks)))

        self._commit_changes()

        # For the caller's benefit, we'll return the tasks that matched
        return self._matching_tasks

    def _set_location_reminder(self, t: todoist.api.models.Item, _r: dict):
        """
        Attaches a reminder object to a given task unless there's already ann existing reminder
        :param t: the task object we'll attach a reminder to
        :param _r: the user provided reminder object we'll parse into the necessary fields for the todoist reminder API
        :return:
        """
        # Todoist is 'dumb' w/ reminders. there are no client or server side duplicate checks, so we must check here.
        _reminders = get_reminders_by_task_id(self.api_client, t['id'])

        # If there are any reminders on the task, we need to check for duplicates
        for _robj in _reminders:
            # If this code has been called since the last .sync() call, then there will likely be objects
            #   in the cache that are linked to the current task but that do not have fully-formed properties.
            # In testing, it appears that the 'type' property is usually not present until _after_ we .sync()
            #   and the id of the object is changed from UUID to numerical ID
            ##
            if 'type' not in _robj:
                continue

            # Check all the user-defined properties against those of the existing _robj.
            #   if they all match, then the reminder is existing and does not need to be created
            if _r['type'] == _robj['type'] and _r['service'] == _robj['service'] and \
                    _r['where']['name'] == _robj['name'] and \
                    str(_r['where']['latitude']) == str(_robj['loc_lat']) and \
                    str(_r['where']['longitude']) == str(_robj['loc_long']) and \
                    _r['where']['trigger'] == _robj['loc_trigger'] and \
                    _r['where']['radius'] == _robj['radius']:

                self.log.debug("There is already a matching {} reminder, not creating duplicate!".format(_r['type']))
                # return the ID of the existing reminder
                return _robj['id']

        # If we didn't bail, reminder needs to be created
        self.log.debug("adding {type} reminder via {service} for {lname}@{lat}/{lon} to _task:{tid}/{tname}".format(
            type=_r['type'],
            service=_r['service'],
            lname=_r['where']['name'],
            lat=_r['where']['latitude'],
            lon=_r['where']['longitude'],
            tid=t['id'],
            tname=t['content'],
        )
        )

        _r = self.api_client.reminders.add(
            t['id'], service=_r['service'], type=_r['type'], name=_r['where']['name'],
            loc_lat=str(_r['where']['latitude']),
            loc_long=str(_r['where']['longitude']),
            loc_trigger=_r['where']['trigger'],
            radius=_r['where']['radius'])
        self._emit_event('reminder_add', _r)

        return _r

    def _set_absolute_reminder(self, t: todoist.api.models.Item, _r: dict):
        """
        Attaches an absolute reminder to a task ID.
        :param t: the task object we'll attach a reminder to
        :param _r: the user provided reminder object we'll parse into the necessary fields for the todoist reminder API
        :return:
        """
        ##
        # The todoist API is pretty basic; the client (read: me) must do a lot of validation to prevent random/silent
        #   errors/failures. When setting an absolute reminder, we must make sure that the reminder is not already
        #   in the past.
        ##
        # User will provide a date/time stamp that may or may not have a timezone offset.
        # In any event, we try to parse it, then localize it to the users configured timezone
        ##
        # First, figure out when NOW is
        _user_tz = timezone(self.client_config['client']['timezone'])
        _now = _user_tz.localize(datetime.now())

        # Parse the datetime user wants reminder fired off at
        _absolute_dt = dateutil.parser.isoparse(_r['when'])

        # We need to confirm that _absolute_dt is in the future
        self.log.debug("Checking that _absolute_dt: {} is ahead of _now: {}...".format(_absolute_dt, _now))
        if _now > _absolute_dt:
            self.log.warning("Absolute Reminder for {} is in the past, won't create reminder".format(_absolute_dt))
            return False

        # The user has asked for a reminder at a time that is in the future... now make sure there isn't a reminder
        #   already created for the same time
        ##
        self.log.debug("... it is! Checking for existing reminders for {}".format(_absolute_dt))

        # Get all the reminders for the task in question
        _reminders = get_reminders_by_task_id(self.api_client, t['id'])

        ##
        # We need to check to see if there is already an absolute reminder for this task
        for _robj in _reminders:
            if 'type' not in _robj:
                continue

            # Check the type and service to see if we are in the right ballpark...
            if _r['type'] == _robj['type'] and _r['service'] == _robj['service']:
                # We have a reminder for the task that is of the same type and service... now we need to check
                #   the date of the reminder
                ##
                _reminder_dt = get_tz_aware_task_due_date(_robj, _user_tz)

                # Check if the localized reminder_dt == the absolute_dt
                self.log.debug("checking if _reminder_dt:{} matches _absolute_dt:{}".format(_reminder_dt, _absolute_dt))
                if _reminder_dt == _absolute_dt:
                    self.log.debug("There is already a {} reminder via {} for {} on task. Won't create additional"
                                   .format(_robj['type'], _robj['service'], _reminder_dt))
                    # return the ID of the existing reminder
                    return _robj['id']

        # Otherwise, we DONT have the same absolute time, so make the reminder....
        self.log.debug("adding {type} reminder via {service} for {when} to _task:{tid}/{tname}".format(
                type=_r['type'],
                service=_r['service'],
                when=_r['when'],
                tid=t['id'],
                tname=t['content']
        )
        )
        # Note: Todoist appears to *only* support relative dates for reminders.
        # This means that we need to strip the timezone offset from _absolute_dt.
        #   E.G.: 2020-06-16 12:58:00-07:00 must become 2020-06-16 12:58:00
        #   and then the todoist client will fire off a reminder at 12:58:00 in the TZ that the user is in
        #
        # See: https://strftime.org/
        _when = _absolute_dt.strftime('%Y-%m-%dT%H:%M:%S')

        _r = self.api_client.reminders.add(t['id'], service=_r['service'], due={'date': _when})
        self._emit_event('reminder_add', _r)

        return _r

    def _set_relative_reminder(self, t: todoist.api.models.Item, _r: dict):
        """
        Attaches a relative reminder to a task ID. relative in that the reminder is relative too the due date of the
            task. E.G.: 15 min before the task is due.
        :param t: the task object we'll attach a reminder to
        :param _r: the user provided reminder object we'll parse into the necessary fields for the todoist reminder API
        :return:
        """
        ##
        # The todoist API is pretty basic; the client (read: me) must do a lot of validation to prevent random/silent
        #   errors/failures. When setting a relative reminder, we must make sure that the task due time/date minus
        #   the relative reminder is still in the future.
        #
        # E.G. Task is due today@13:00. If we want to set a 'relative' reminder to 15 min before the task is due,
        #   we need to make sure that 13:00h-15m (12:45) is still ahead of now(). If now() is 12:50, then we can't
        #   possibly remind the user 15m before the task due date as 12:50 is 5 min past when thee reminder would have
        #   been fired off.
        ##
        # Get now() localized to user configured TimeZone
        _user_tz = timezone(self.client_config['client']['timezone'])
        _now = _user_tz.localize(datetime.now())

        # Get the task due date/time localized to the user as well
        _task_dd = get_tz_aware_task_due_date(t, _user_tz)

        # We can't schedule a reminder for a task with no due date
        if _task_dd is None:
            _e = "Can't set relative reminder on task://{} ({}) because due:None".format(t['id'], t['content'])
            self.log.error(_e)
            return False

        # Figure out when the relative reminder would be fired off
        self.log.debug("calculate timedelta of {} min from _task_dd:{}".format(_r['minutes'], _task_dd))
        _td = timedelta(minutes=_r['minutes'])
        _relative_reminder_dt = _task_dd - _td
        self.log.debug("_relative_reminder_dt: {}".format(_relative_reminder_dt))

        # Check if there are any relative reminders for the task that have the same due date
        _reminders = get_reminders_by_task_id(self.api_client, t['id'])

        ##
        # We need to check to see if there is already an absolute reminder for this task
        for _robj in _reminders:
            if 'type' not in _robj:
                continue

            # Check for dupe...
            if _r['type'] == _robj['type'] and _r['service'] == _robj['service'] \
                    and _r['minutes'] == _robj['minute_offset']:
                self.log.debug("matching type and service. Won't create duplicate!")
                return _robj['id']

        self.log.debug("adding {type} reminder via {service} for {when} min from now to _task:{tid}/{tname}".format(
            type=_r['type'],
            service=_r['service'],
            when=_r['minutes'],
            tid=t['id'],
            tname=t['content']
        )
        )

        _r = self.api_client.reminders.add(t['id'], service=_r['service'], minute_offset=_r['minutes'])
        self._emit_event('reminder_add', _r)
        return _r

    def _remove_label_name_match(self, t: todoist.api.models.Item, filter_obj: dict):
        return remove_component_by_ids(self.api_client, t, filter_obj, component='labels', attribute='name')

    def _remove_task_title_match(self, t: todoist.api.models.Item, filter_obj: dict):
        return remove_component_attribute_by_regex(t, filter_obj, component='task', attribute='content')
