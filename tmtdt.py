# tdt.actions has a map of action_name -> Class

import tdt.actions
# Importlib dynamically loads the class :)
import importlib

# Config parse/validators
from tdt.utils.cache import reset_local_state
from tdt.utils.config import process_config, validate_job_file, get_todoist_file, validate_args

# Version String for args
from tdt.version import __version__

# Various ways that todoist can break..
from tdt.exceptions import TodoistClientError
from tdt.exceptions import TDTException

import argparse

# The todoist library
import todoist

# Debugging
import logging


def launch(args: argparse.Namespace):
    """
    :param args: the argparse args
    :return:
    """
    # Go through the parsed CLI args and configure each portion of the tool as needed
    process_config(args)

    # After processing the args, we have logging!
    log = logging.getLogger(__name__)

    # We can be confident that the job-file exists, but we've not yet confirmed that it contains valid tdt commands
    job_file = args.job_file

    # If nothing blows up, then we get back a list of job objects
    valid_actions = validate_job_file(job_file)
    log.info("🟩 Have '{}' valid actions.".format(len(valid_actions)))

    # Before we can begin processing actions, we'll need to load additional basic API client and additional
    #   user-configured settings for working w/ todoist objects
    client_config = get_todoist_file(args.config_file)

    # Use that API token to get a client
    todo_client = todoist.TodoistAPI(client_config['todoist']['api']['token'])

    # Check if we have been told ot clear local cache
    if args.reset_state:
        reset_local_state(todo_client)
        log.info("Exiting. Please re-run job...")
        exit()

    log.info("⚙️ Spinning up Todoist API Client...")

    # And, before we do anything, make sure that we have a totally valid API token and an UTD cache
    result = todo_client.sync()
    # We need to check if there's a `sync_token` field in the dict that comes back. If there is, we managed to sync
    #   correctly. If there is not, then we need to assume that something went wrong and the resp will explain what...
    ##
    if 'sync_token' not in result:
        _e = "ToDoist Didn't like request to Sync. Is your API_TOKEN correct?. Got back:{}".format(result)
        # See: https://developer.todoist.com/sync/v8/?python#response-status-codes
        log.fatal(_e)
        raise TodoistClientError(_e)

    # Yay, nothing blew up! Begin actually iterating over the actions...
    _idx = 0

    # Keep track of which action(s) encountered some sort of problem
    _problems = []
    for action_block in valid_actions:
        # Iterate over each action block and pull some details from the action_block to make the following code
        #   much easier to read.
        ##
        # User defined name for the action block
        action_block_name = action_block['name']
        # The actual resource_action to take
        resource_action = action_block['action']
        # ignore switch
        action_enable = action_block['enabled']

        # Each action in a job file can be independently toggled on/off
        if action_enable is False:
            log.warning("⏭️ Skip #{} {}://{} as it's disabled ...".format(_idx, resource_action, action_block_name))
            _idx += 1
            continue
        else:
            log.info("🏁 Executing #{} {}://{}...".format(_idx, resource_action, action_block_name))

        ##
        # Use the action_name from the jobs file to programmatically load the correct class.
        # See: https://stackoverflow.com/questions/4821104/dynamic-instantiation-from-string-name-of-a-class-in-dynamically-imported-module
        ##
        # action_name is a string composed of a 'resource class' followed by the actual verb w/i that class.
        #   E.G.: label_create is a create action of resource class label
        ##
        # device the resource into tokens. E.g. label_apply -> label, apply
        _rt = resource_action.split("_")
        # Take the tokens to build the path to the package
        _action_mod_name = "tdt.actions.{}.{}".format(_rt[0], _rt[1])

        # Now, we know which package too load, but within that package, what class do we load to do the needful?
        if resource_action not in tdt.actions.action_map:
            _e = "No class mapped to 'resource_action':{}".format(resource_action)
            log.error(_e)
            log.debug("have {}".format(tdt.actions.action_map.keys()))
            raise TDTException(_e)

        _action_class = tdt.actions.action_map[resource_action]

        # We now know which package, module, class too load :)
        log.debug("resource_action '{}' handled from '{}.{}'".format(resource_action, _action_class, _action_mod_name))

        # Use importlib to load the module, complete w/ the class_name (or die trying)
        try:
            # Load the module
            _action_mod = importlib.import_module(_action_mod_name)

            # Get a class _from_ the module
            action_handler_class = getattr(_action_mod, _action_class)

            # Make instance of class
            action_handler = action_handler_class()

            # Configure the API client for the handler...
            action_handler.api_client = todo_client
            # Downloading backups requires the API token. Rather than hack the todo_client and try to get it out
            #   that way, much easier to just pass it in :)
            action_handler.api_token = client_config['todoist']['api']['token']

            # ... and pass in the client params
            action_handler.client_config = client_config

            # ... and pass in the command line args (dry run?)
            action_handler.cli_args = args

            # And finally, do_work on the action from thee job file
            result = action_handler.do_work(action_block)

            # Log if the action completed successfully or not
            log.info("☑️ DONE with action({})://{} ({})...".format(_idx, resource_action, action_block_name))
            if result is False:
                # If *anything* didn't go according to plan, record the problem action
                _problems.append(action_block)
                # And tell the user
                log.info("... However, a non-fatal error did occur. ⭕")
            else:
                # And tell the user
                log.info("... And nothing went wrong! ✅")

            # In any event, increase idx and move on
            _idx += 1

        # Blow up if the module couldn't be found
        except ModuleNotFoundError as mnfe:
            _e = "Unable to validate the resource_action '{}' because the _action_mod_name '{}' could not be found. " \
                 "mnfe:{} ".format(resource_action, _action_mod_name, mnfe)
            log.error(_e)
            raise TDTException(_e)

    log.info("Execution of job://{} complete. Goodbye! 👋".format(job_file))


def parse_args():
    """
    This script does very little, so there's not much to configure. Additionally, what can be configured
        is likely not going to change often so it's best to just leave things in a config file.
    :return:
    """

    # Root argparse
    parser = argparse.ArgumentParser(
        description='Collection of tools to automate the upkeep of ToDoist',
        epilog='Push that blue button...',
        allow_abbrev=False)

    parser.add_argument('--version', action='version', version=__version__)

    ###
    # LOGGING
    ###
    _log_default = 'INFO'
    parser.add_argument('--log-level',
                        default=_log_default,
                        choices=logging._nameToLevel.keys(),
                        help='Set log level. Defaults to {}'.format(_log_default)
                        )

    parser.add_argument('--log-file',
                        default=None,
                        type=str,
                        help='if set, the path to log to. If not set, stdout is used'
                        )

    ###
    # JOBS
    ###
    _job_default = './jobs/demo/00.setup.yaml'
    parser.add_argument('--job-file',
                        default=_job_default,
                        type=str,
                        help='Path to the job file. Defaults to {}'.format(_job_default)
                        )

    ###
    # Todoist
    ###
    _config_default = './config/config.yaml'
    parser.add_argument('--config-file',
                        default=_config_default,
                        type=str,
                        help='Path to TMDT config file. Defaults to {}'.format(_config_default)
                        )

    ###
    # DEV/TEST
    ###
    parser.add_argument('--dry-run',
                        action='store_true',
                        help='Skips over every call to commit changes back to ToDoist'
                        )

    parser.add_argument('--reset-state',
                        action='store_true',
                        help='Use to clear local todoist state and exit'
                        )

    return parser.parse_args()


if __name__ == '__main__':
    # Begin by parsing any arguments from the client
    args = parse_args()

    # Perform BASIC validation of the arguments
    validate_args(args)

    # Assuming that nothing has blown up, we launch the tool
    launch(args)

    # And assuming that nothing there blew up, we exit
    exit(0)
