###
# A set of util functions to make working with the todoist API a bit easier
##

from datetime import datetime, date

import todoist

import logging

from tdt.exceptions import TDTException

# All searches are done as regex
import re

from pytz import timezone

from tdt.utils.date import get_tz_aware_task_due_date

# Debugging
from prettyprinter import pprint as pp

def get_tasks_by_title_with_regex(client: todoist.TodoistAPI, pattern: re.Pattern):
    """
    Simple helper function that compares all task.titles against a regex

    :param pattern: The regex pattern to filter
    :param  client: The todoist client

    :return:
    """
    log = logging.getLogger(__name__)

    log.debug("Filtering tasks by title for pattern:`{}`...".format(pattern))

    # The tasks that match will be added here and then returned to caller
    matching_tasks = []

    for t in client['items']:
        # Pull out the "content" of the item
        _name = t['content']

        # Attempt to correct for some data corruption i managed to cause while testing/developing:
        #   thee _name of a task was turned into a non-string object!
        # Remedy is to delete() it, but i'll keep that commented out and just go w/ an error for now
        try:
            _match = pattern.search(_name)
            if _match:
                matching_tasks.append(t)
        except TypeError as ve:
            # make noise, but don't do anything unless i specifically come back in here to delete
            _e = "task://{} content content has been corrupted!".format(t['id'])
            log.error(_e)
            continue
            # t.delete()
            # exit()

    log.debug("returning {} tasks by title.".format(len(matching_tasks)))
    return matching_tasks


def get_tasks_by_label_id(client=todoist.TodoistAPI, find=int):
    """

    :param client:
    :param find:
    :return:
    """
    log = logging.getLogger(__name__)

    if type(find) is not int:
        _e = "Invalid Query. Find must be INT. Got:`{}``".format(find)
        raise ValueError(_e)

    log.debug("Filtering tasks by label for needle:`{}`...".format(find))

    # The tasks that match will be added here and then returned to caller
    matching_tasks = []

    for t in client['items']:

        # Pull out the "content" of the item
        _labels = t['labels']
        if find in _labels:
            matching_tasks.append(t)

    log.debug("returning {} tasks by label".format(len(matching_tasks)))
    return matching_tasks


def get_relevant_tasks(client: todoist.TodoistAPI, filters: dict, assumed_tz: timezone):
    """
    A high-level function that takes the user provided, validated filters object and gathers the appropriate tasks
        based on the selection criteria in the filter(s).

    All tasks that match will be  returned to the caller.

    :param client:  The todoist client
    :param filters: The dict of task/label strings
    :param assumed_tz: The client's assumed/local time-zone
    :return:
    """
    log = logging.getLogger(__name__)

    ##
    # After a lot of deliberation, I've decided to go all out on how searching works.
    # The user can supply multiple filter objects. The _result_ of each filter will be ORd together.
    # Within each filter, the user can limit matches by task title AND label name AND project name.
    #
    # This means that we just need to step through each filter object, pass the query off to a helper function that
    #   processes the individual restrictions in the filter object and then combine all the tasks into one list.
    #
    ##
    # Collect all tasks from each filter
    _all_tasks = set()
    _all_selectors = []
    # TODO: May be able to improve performance here w/ threads

    for f in filters:
        # get the tasks and the selector(s) that 'originated' the task
        _tasks, _selectors = _do_search(client, f, assumed_tz)
        ##
        # In order to properly honor the option.remove flag from each filter, we _also_ need to keep track of
        #   which filter block 'matched' the tasks.
        _all_tasks.update(_tasks)
        _all_selectors.append(_selectors)

    log.info("🧮 Found a grand total of '{}' relevant task(s)...".format(len(_all_tasks)))
    return _all_tasks, _all_selectors


def _do_search(client: todoist.TodoistAPI, filter_obj: dict, tz: timezone('UTC')):
    """
    Actually does the dirty work of processing a filter object
    :param filter:
    :return:
    """
    log = logging.getLogger(__name__)

    # For now, we only support retrieving tasks by title, label. In the future, i'd like to support:
    #   - by comment
    #
    # Additionally, the user can limit the search to certain projects. In the future, i'd like to support:
    #   - by shared/assigned
    #   - ?? Pending feedback from community...
    ##
    # Store the tasks from each type of query as a set... but only if that type of query is used!
    _tasks_by_title = False
    _tasks_by_date = False
    _tasks_by_label = False
    _tasks_by_project = False

    ##
    # Because each selector in each filter block has options, we need to  also record which selector block matched
    #   which tasks. E.G.: if a task.title.match: 'at some place' results in task #12345, called
    #   "do thing at some place" being added to the search results, we need to store that task 12345 is in the results
    #   *because* of the task.title.match. This is because we must honor the various options attached to a given filter.
    #
    # If the task.title.option.remove flag was set, then after doing the 'action'
    #   (example, apply the label @at_some_place), the matching string 'at some place' should be removed from the
    #   task.title so that task 12345 goes *FROM* 'do thing at some place' to 'do thing @at_some_place'
    #
    # To facilitate this, we add the task ID for every 'match' in the title, label, project searches to a list.
    # After we have ANDed every set of tasks together and produced the _final_ set of tasks that matches EVERY filter
    #   criteria, we then must pair up each task ID with the selector(s) that resulted in the task selection.
    #
    ##
    # Store the task IDs that each selector in the filter resulted in
    _task_ids_by_title = False
    _task_ids_by_date = False
    _task_ids_by_label = False
    _task_ids_by_project = False

    # The complete set of results that matches all selectors in the filter
    _all_tasks = set()

    # If the user has passed in any regex_options, we need to parse them back into bitflags
    _re_flags = parse_regex_options(filter_obj)

    # At this point, we're now ready to start looking for tasks!
    ##
    ##
    # Note: it might be more performant to change the order around. If there's a project limit, start w/ that
    ##
    # Start with the title, we support TWO selectors for task: title and date
    if 'task' in filter_obj:
        # This code is starting to get really harry/long. It's hard too kep track of everything that this one function
        #   does on disk.
        # TODO: refactor this. I think a generic utils package and from that make a search() class which
        #   can then use similar reflection techniques to spin up the right search sub class. Search gooes through
        #   each filter and walks each type of filter to find the right method for the given selector
        ##
        # For now, just to prototype the code for dates, we'll do it here
        ##
        if 'content' in filter_obj['task']:
            _tasks_by_title = set()
            _task_ids_by_title = []
            # Build the task title query
            _task_title_re = re.compile(filter_obj['task']['content']['match'], flags=_re_flags)
            log.debug("👀 Searching for tasks that contain `{}` in their title...".format(_task_title_re))

            # Fire off the query to get all matching tasks... we'll further reduce the results (if needed) later
            _tasks_by_title.update(get_tasks_by_title_with_regex(client, _task_title_re))
            log.debug("{} contains {} tasks".format('_tasks_by_title', len(_tasks_by_title)))

            for _t in _tasks_by_title:
                _task_ids_by_title.append(_t['id'])
            log.debug("{} contains {} tasks".format('_task_ids_by_title', len(_tasks_by_title)))

        if 'date' in filter_obj['task']:
            _tasks_by_date = set()
            _task_ids_by_date = []

            # The user can select tasks by date with three operators:
            #   - no due date
            #   - relative to some date
            #   - exactly some date/time
            #
            # At validation time, the explicit and relative dates are turned into datetime objects.
            # In the event that the user provided a simple date, there will be no localization information attached to
            #   the datetime object. We'll fix that now so the search logic below can remain consistent
            ##
            # If the user specified Absent, then we search for tasks with a due property of None
            _when = False
            _direction = None

            if 'absent' in filter_obj['task']['date']:
                _when = None
                logging.debug("Searching for tasks with a Due Date of '{}'".format(_when))

            # Searching for tasks w/ a due date
            else:
                for x in ['relative', 'explicit']:
                    if x in filter_obj['task']['date']:
                        _when = filter_obj['task']['date'][x]
                        _direction = _when['direction']
                        logging.debug("Searching for tasks with a {} Due Date of '{}'...".
                                      format(x, _when, _direction))

            # Make sure we didn't miss a case
            if _when is False:
                logging.error("Somehow _when was never properly set! Can't continue")
                return False

            # _when will look like one of:
            # None
            # {'to': datetime.datetime(2020, 6, 18, 14, 57, 39, 272490), 'direction': 'before'}
            # {'to': datetime.datetime(2020, 5, 20, 14, 27, 19,
            #   tzinfo=datetime.timezone(datetime.timedelta(seconds=43200))), 'direction': 'after'}
            ##
            # Add timezone info if the user didn't already do so
            if _when is not None:
                # Alias is shorter
                _w = _when['to']

                # Check if date
                if isinstance(_w, date):
                    # Cast to datetime, pick up time objects so we can localise
                    _w = datetime(_w.year, _w.month, _w.day)

                logging.debug("checking for tzinfo...")
                if not hasattr(_when, 'tzinfo'):
                    logging.debug("Localizing to user TimeZone: '{}'".format(tz))
                    _w = tz.localize(_w)
                _when = _w

            log.info("👀 Searching for tasks that occurred '{}' the date `{}`...".format(_direction, _when))
            for t in client['items']:

                # Pass in the task and the user's local timezone to get back
                #   a localized task due date or None if the task has no due date
                ##
                _ltd = get_tz_aware_task_due_date(t, tz)

                # There are two variables that we need to compare, each can have two values, so there's 4 cases.
                # _ltd is None or some DateTime object
                # _when is None or some DateTime object
                #
                # If _when is None and _ltd is None, we have a match, else, we....
                ##
                # Are we in the case where the user wants None for due date?
                if _when is None and _ltd is None:
                    # Task is None and this is what User wants
                    _tasks_by_date.add(t)
                    _task_ids_by_date.append(t['id'])
                    continue

                elif _when is None and _ltd is not None:
                    # User wants None, but task is not None
                    continue

                # We now know that _when is not None, but what about _ltd?
                if _ltd is None:
                    # User does not want None, but task is None
                    continue

                # _when is not None and _ltd is not None... so lets orient ourselves to the _when and _ltd
                if _direction == 'before':
                    if _ltd < _when:
                        log.debug("Task:{} is due on {} which is {} the _when:{}".format(t['content'], _ltd,
                                                                                         _direction, _when))
                        _tasks_by_date.add(t)
                        _task_ids_by_date.append(t['id'])
                        continue
                if _direction == 'after':
                    if _ltd > _when:
                        log.debug("Task:{} is due on {} which is {} the _when:{}".format(t['content'], _ltd, _direction,
                                                                                         _when))
                        _tasks_by_date.add(t)
                        _task_ids_by_date.append(t['id'])
                        continue

    # Follow up with labels
    if 'labels' in filter_obj:
        _tasks_by_label = set()
        _task_ids_by_label = []
        # We must check if the user has explicitly told us to search for UNLABELED tasks or not.
        # If the user has not, then the query by label involves an additional step:find out all the labels that match
        #   a given regex query and then turn each matching label into jus a label_id which we will then use
        #   to identify all the tasks that have the associated label_id(s)
        ##
        # If th user asks for tasks w/ no label, then find all tasks w/ no labels :)
        if 'absent' in filter_obj['labels']:
            log.debug("user has told us to find tasks with NO LABEL")
            for t in client['items']:
                if len(t['labels']) < 1:
                    _tasks_by_label.add(t)

        else:
            # Build regex for label lookup
            _label_title_re = re.compile(filter_obj['labels']['name']['match'], flags=_re_flags)

            # Get the labels. If we don't have any matches, then we abort now.
            # It's impossible for the user to specify a label filter *and* expect tasks back if the
            #   label filter has no results because of the AND nature of inter-filter selectors.
            #
            # If the user wanted to find tasks with _no_ label then they should use the explicit absent: Yes flag
            ##
            log.info("👀 Searching for tasks with labels matching: {}...".format(_label_title_re))
            _matching_labels = get_components_by_name_with_regex(client, 'labels', _label_title_re)

            if len(_matching_labels) > 0:
                # We have found some set of labels that match the regex. Now we must pull out the label IDs!
                log.info("... found {} Labels matching the selectors".format(len(_matching_labels)))
                _matching_label_ids = [_p['id'] for _p in _matching_labels]

                # List comprehension syntax gets UGLY if you go more than 1 level so write this out in a readable way
                ##
                for t in client['items']:
                    for _l in t['labels']:
                        if _l in _matching_label_ids:
                            _tasks_by_label.add(t)

        # We now have all tasks by matching label
        log.debug("{} contains {} tasks".format('_tasks_by_label', len(_tasks_by_label)))
        for _t in _tasks_by_label:
            _task_ids_by_label.append(_t['id'])
        log.debug("{} contains {} tasks".format('_task_ids_by_label', len(_task_ids_by_label)))

    # Check if the user has set any project level query
    if 'projects' in filter_obj:
        _tasks_by_project = set()
        _task_ids_by_project = []
        # Build the task title query
        _project_title_re = re.compile(filter_obj['projects']['name']['match'], flags=_re_flags)
        log.info("👀 Searching for projects that contain `{}` in their title...".format(_project_title_re))

        # Fire off the query to get all matching projects
        _matching_projects = get_components_by_name_with_regex(client, 'projects', _project_title_re)
        log.debug("_projects_by_title contains {} tasks".format(len(_matching_projects)))

        if len(_matching_projects) > 0:
            # We have found some set of projects that match the regex. Now we must pull out the project IDs!
            log.info("... found {} Projects matching the selectors".format(len(_matching_projects)))
            _matching_project_ids = [_p['id'] for _p in _matching_projects]

            # List comprehension also gts ugly w/ conditionals :/
            ##
            for t in client['items']:
                if t['project_id'] in _matching_project_ids:
                    _tasks_by_project.add(t)

        # We now have all tasks by matching label
        log.debug("{} contains {} tasks".format('_tasks_by_project', len(_tasks_by_project)))
        for _t in _tasks_by_project:
            _task_ids_by_project.append(_t['id'])
        log.debug("{} contains {} tasks".format('_task_ids_by_project', len(_task_ids_by_project)))

    # At this point in time, we have three variables that are either type set or False.
    # We AND the sets together and return what's left :)
    ##
    log.debug("Applying *AND* to matching task sets...")
    # Won't get expected behavior if AND the empty _all_tasks with the first non-empty set, so we must find the first
    #   non false set and use that as the 'starter'
    ##
    if _tasks_by_title is not False:
        log.debug("using {} as starter for _all_tasks ({})...".format('_tasks_by_title', len(_tasks_by_title)))
        _all_tasks = _tasks_by_title
    if _tasks_by_date is not False:
        log.debug("using {} as starter for _all_tasks ({})...".format('_tasks_by_date', len(_tasks_by_date)))
        _all_tasks = _tasks_by_date
    elif _tasks_by_label is not False:
        log.debug("using {} as starter for _all_tasks ({})...".format('_tasks_by_label', len(_tasks_by_label)))
        _all_tasks = _tasks_by_label
    elif _tasks_by_project is not False:
        log.debug("using {} as starter for _all_tasks ({})...".format('_tasks_by_project', len(_tasks_by_project)))
        _all_tasks = _tasks_by_project

    # Now that we have our starter, AND all the non-false things :)
    if _tasks_by_title is not False:
        log.debug("ANDing _all_tasks with {}({})...".format('_tasks_by_title', len(_tasks_by_title)))
        _all_tasks = _all_tasks & _tasks_by_title
        log.debug("_all_tasks is now {}...".format(len(_all_tasks)))

    if _tasks_by_date is not False:
        log.debug("ANDing _all_tasks with {}({})...".format('_tasks_by_date', len(_tasks_by_date)))
        _all_tasks = _all_tasks & _tasks_by_date
        log.debug("_all_tasks is now {}...".format(len(_all_tasks)))

    if _tasks_by_label is not False:
        log.debug("ANDing _all_tasks with {}({})...".format('_tasks_by_label', len(_tasks_by_label)))
        _all_tasks = _all_tasks & _tasks_by_label
        log.debug("_all_tasks is now {}...".format(len(_all_tasks)))

    if _tasks_by_project is not False:
        log.debug("ANDing _all_tasks with {}({})...".format('_tasks_by_project', len(_tasks_by_project)))
        _all_tasks = _all_tasks & _tasks_by_project
        log.debug("_all_tasks is now {}...".format(len(_all_tasks)))

    # We _finally_ have a complete set of tasks that matched *all* the selectors in the filter block. We now need
    #   to map the tasks back to the selector(s) that matched them for the callers benefit
    ##
    _source_selectors = {
        'task.content': [],
        'task.date': [],
        'labels.name': [],
        'project.name': []
    }
    log.debug("Mapping {} tasks back to the source selector(s)...".format(len(_all_tasks)))
    for _t in _all_tasks:
        if isinstance(_task_ids_by_title, list):
            if _t['id'] in _task_ids_by_title:
                _source_selectors['task.content'].append(_t['id'])

        if isinstance(_task_ids_by_date, list):
            if _t['id'] in _task_ids_by_date:
                _source_selectors['task.date'].append(_t['id'])

        if isinstance(_task_ids_by_label, list):
            if _t['id'] in _task_ids_by_label:
                _source_selectors['labels.name'].append(_t['id'])

        if isinstance(_task_ids_by_project, list):
            if _t['id'] in _task_ids_by_project:
                _source_selectors['project.name'].append(_t['id'])

    log.debug("_source_selectors.{} has {} tasks".format('title', len(_source_selectors['task.content'])))
    log.debug("_source_selectors.{} has {} tasks".format('date', len(_source_selectors['task.date'])))
    log.debug("_source_selectors.{} has {} tasks".format('label', len(_source_selectors['labels.name'])))
    log.debug("_source_selectors.{} has {} tasks".format('project', len(_source_selectors['project.name'])))

    return _all_tasks, _source_selectors


def get_components_by_name_with_strings(client: todoist.TodoistAPI, component: str, queries: [str]):

    _results = []
    for q in queries:
        _qre = re.compile(q)
        _r = get_components_by_name_with_regex(client, component, _qre)
        # Extending w/ an empty list is a no-op
        _results.extend(_r)

    return _results


def get_components_by_name_with_regex(client: todoist.TodoistAPI, component: str, pattern: re.Pattern):
    log = logging.getLogger(__name__)

    # Make sure the caller is asking for something we know how to  fetch
    if component not in ['labels', 'projects', 'items', 'sections']:
        _e = "Don't know how to query todoist for component:{}".format(component)
        log.error(_e)
        raise TDTException(_e)

    # Ok, sanity confirmed, do the work
    _matches = []

    log.debug("Will look for '{}' matching '{}'...".format(component, pattern))
    # The Todoist API has a Mixin for all()
    for thing in getattr(client, component).all():
        # Most things in todoist have a 'name'. Except tasks (called items) which have a 'content'
        _property = None
        if component == 'items':
            _property = 'content'
        else:
            _property = 'name'

        # Now that we have property figured out, do the matches
        _match = pattern.search(thing[_property])
        if _match:
            _matches.append(thing)
    log.debug("returning {} _matches".format(len(_matches)))
    return _matches


def get_component_by_ids(api_client: todoist.TodoistAPI, component: str, component_ids: [int], strict: bool = False):
    """
    Fetches a given $component by it's ID(s
    :param api_client:
    :param component:
    :param component_ids:
    :param strict:
    :return:
    """
    log = logging.getLogger(__name__)

    # Sanity check
    if len(component_ids) < 1:
        _e = "Can't search for {} with 0 queries! got:{}".format(component, component_ids)
        log.error(_e)
        raise TDTException(_e)

    # Make sure the caller is asking for something we know how to  fetch
    if component not in ['labels', 'projects', 'items', 'sections']:
        _e = "Don't know how to query todoist for component:{}".format(component)
        log.error(_e)
        raise TDTException(_e)

    # Ok, sanity confirmed, do the work
    _matches = []

    log.debug("Will look for '{}' matching {} queries...".format(component, len(component_ids)))
    # The Todoist API has a Mixin for all()
    for thing in getattr(api_client, component).all():
        # Check if the name of $thing is in the  list of queries
        if thing['id'] in component_ids:
            _matches.append(thing)

    # We've made a best effort to find all $component that match each supplied query.
    # Because we used the 'in' operator instead of regex matching, we should expect that one
    #   query string results in one element in _matches if all the $components that we're
    #   searching for are known to exist. This *might* not be the case if the caller is trying
    #   to confirm weather or not a given component exists. The caller can set the 'strict'
    #   flag to indicate if this should be considered an error or not
    ##
    _lq = len(component_ids)
    _lm = len(_matches)
    if _lq != _lm:
        log.warning("⚠️ Length of _matches ({}) but ({}) _queries provided. Perhaps some '{}' do not yet exist?"
                    .format(_lm, _lq, component))

        if strict:
            log.error("🚨 returning no {} due to mismatch lengths and strict set to {}".format(component, strict))
            return []

    log.debug("...returning {} {}".format(len(_matches), component))
    return _matches


def delete_component_by_ids(api_client: todoist.TodoistAPI, component: str, component_ids: [int]):
    log = logging.getLogger(__name__)

    _components = [
        'labels',
        'projects',
        'items'

    ]

    # Make sure the caller is asking for something we know how to  fetch
    if component not in _components:
        _e = "Don't know how to delete component:{}. Supported:{}".format(component, _components)
        log.error(_e)
        raise TDTException(_e)

    # The Todoist API has a Mixin for
    for _cid in component_ids:
        log.debug("fetching {}://{}".format(component, _cid))
        _c = getattr(api_client, component).get_by_id(_cid)

        # Check if the name of $thing is in the  list of queries
        if _c is not None:
            log.info("️🗑 deleting {}://{}".format(component, _cid))
            _c.delete()
        else:
            _e = "Something's gone HORRIBLY WRONG. _c is None! Was hoping to get {}://{}".format(component, _cid)
            raise TDTException(_e)


def parse_regex_options(filter_obj: dict):
    """
    If the user chooses, they can pass in regex options. They'll pass in options as a list of strings that represent
        the flags that we'll neeed to pass to the regex calls. We turn the strings into the actual flags.

    :param filter_obj:
    :return:
    """
    # We can safely assume that voluptuous has already done the validation which reduces the scope of concern.
    # There will be a list of strings which we map to individual flags and OR together or there will be no options :)
    ##
    _flags = 0
    if 'regex_options' not in filter_obj:
        return _flags

    if len(filter_obj['regex_options']) > 0:
        # User provides string, we need to turn back into actual constant/flags from the re object
        for _regex_opt in filter_obj['regex_options']:
            _f = getattr(re, _regex_opt.split(".")[1])
            _reg_flags = _flags | _f

    return _reg_flags
