"""
    Functions for working w/ the reminders
"""
import todoist

# Debugging
from prettyprinter import pprint as pp


def get_reminders_by_task_id(api_client: todoist.api.TodoistAPI, task_id: int):
    """
    Util function that searches for all reminder objects associated w/ a given task
    :param api_client:
    :param task_id:
    :return:
    """

    # All the reminders that we find
    _reminders = []
    for _r in api_client.reminders.all():
        if _r['item_id'] == task_id:
            _reminders.append(_r)

    return _reminders
