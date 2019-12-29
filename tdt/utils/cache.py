"""
    Collection of functions useful for working w/ local Todoist API Client Cache
"""
import shutil
import logging


def reset_local_state(todo_client):
    """
    Helper function to reset state on todoist API and delete the local data-store file(s)
    :param todo_client:
    :return:
    """
    log = logging.getLogger(__name__)
    # *something* in the local cache is FUBAR. Solution is to
    #   reset todoist api client state and then delete the on-disk data
    ##
    log.warning("Clearing local todoist cache...")
    todo_client.reset_state()
    log.warning("...Done! Deleting '{}'...".format(todo_client.cache))
    shutil.rmtree(todo_client.cache)
    log.warning("...Done!".format(todo_client.cache))
