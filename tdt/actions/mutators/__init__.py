##
# When mutating a task, there are only two (currently, supported) ways to do it
# You'll either remove something EXPLICIT from a task, like label://12345678
#       OR
#   you'll remove something with multiple 'tokens' from some free-form field, like
#   remove any portion(s) of the title that matches a given regex
##
import logging
import re

import todoist

from tdt.actions.utils import parse_regex_options, get_components_by_name_with_regex


# debugging
from prettyprinter import pprint as pp

log = logging.getLogger(__name__)


def remove_component_attribute_by_regex(t: todoist.api.models.Item, filter_obj: dict, component: str, attribute: str):
    """
    Operates on a  given task, removes all matches on the component/property of the task.
    Currently, only the title component is supported

    :param t: The todoist task item
    :param filter_obj:
    :param component: The component of the task item to modify
    :param attribute:
    :return:
    """

    # What we're searching for
    _query = filter_obj[component][attribute]['match']
    log.debug("searching thorough '{}.{}' for '{}'".format(component, attribute, _query))
    # TODO: The code below is mostly a dupe of the label.name search code from utils.py->do_search()
    #   I'll want to refactor the search code out int individual modules, too so that i can just call the
    #   search() method on the Name class from the tdt.search.label package :)
    #
    # For now, we just live w/ the duplication :(
    ##
    # get regex flags from the filter object
    _re_flags = parse_regex_options(filter_obj)

    # Build regex for label lookup
    _query_re = re.compile(_query, flags=_re_flags)

    # Anything that matches _query_re in t['content'] replace with ''
    t[attribute] = re.sub(_query_re, '', t[attribute]).strip()

    # Set the value of _component directly to the thing we're updating
    _kwa = {attribute: t[attribute]}
    # Dump the kwargs for debugging :)
    log.debug("_kwa :{}".format(_kwa))
    return t.update(**_kwa)


def remove_component_by_ids(api_client: todoist.api.TodoistAPI, t: todoist.api.models.Item, filter_obj: dict,
                            component: str, attribute: str):

    # What we're searching for
    _query = filter_obj[component][attribute]['match']
    log.debug("searching thorough '{}.{}' for '{}'".format(component, attribute, _query))

    # get regex flags from the filter object
    _re_flags = parse_regex_options(filter_obj)

    # Build regex for label lookup
    _query_re = re.compile(_query, flags=_re_flags)

    _matches = get_components_by_name_with_regex(api_client, component, _query_re)

    if len(_matches) < 0:
        _e = "Was called to delete '{}.{}' matching '{}' but got no _matches".format(
            component, attribute, _query_re)
        log.fatal(_e)
        # We _really_ should not be here / PANIC!
        raise Exception(_e)

    # We have found some set of components that match the regex. Now we must pull out the component IDs!
    _matching_component_ids = [_obj['id'] for _obj in _matches]
    log.info("... found '{}' '{}' matching the query".format(len(_matching_component_ids), component))

    # Turn the match IDs into a set
    _matching_component_ids = set(_matching_component_ids)
    log.debug("_matching_component_ids:{}".format(_matching_component_ids))
    # Turn the component_ids on the task into a set
    _component_ids_in_task = set(t[component])
    log.debug("_component_ids_in_task:{}".format(_component_ids_in_task))

    # Figure out which _component(s) overlap between the task and the search results
    _common = _matching_component_ids & _component_ids_in_task
    log.debug("_common:{}".format(_common))
    # remove the common from _component_ids_in_task
    _remaining = _component_ids_in_task - _common
    log.debug("_remaining:{}".format(_remaining))

    # Set the value of _component directly to the thing we're updating
    _kwa = {component: list(_remaining)}
    # Dump the kwargs for debugging :)
    log.debug("_kwa :{}".format(_kwa))
    return t.update(**_kwa)
