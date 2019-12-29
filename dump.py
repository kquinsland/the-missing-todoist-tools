import argparse
import json

# The todoist library
import todoist

# Debugging
from prettyprinter import pprint as pp

from tdt.utils.config import get_todoist_file


# Complete dump from the API obj
# TODO: can i pull this dynamically from the API client?
components = [
    'items',
    'biz_invitations',
    'collaborators',
    'collaborator_states',
    'filters',
    'invitations',
    'labels',
    'live_notifications',
    'locations',
    'notes',
    'projects',
    'project_notes',
    'reminders',
    'sections',
    'user',
    'user_settings',
    'activity',
    'backups',
    'business_users',
    'completed',
    'emails',
    'quick',
    'templates',
    'uploads'
]


def launch(args: argparse.Namespace):
    """
    :param args: the argparse args
    :return:
    """
    # Pull a few things out of args for easier access
    _cmp = args.component
    _id = args.id
    _json = args.json

    # Pull out / parse the config file
    client_config = get_todoist_file(args.config_file)

    # Use that API token to get a client
    todo_client = todoist.TodoistAPI(client_config['todoist']['api']['token'])

    if args.do_sync:
        print("doing sync...")
        result = todo_client.sync()
        pp(result)

    # Otherwise, get the manager for that component
    _manager = getattr(todo_client, _cmp)

    if args.id is None:

        if _json:
            # Collect all the JSON friendly bits of all the objects
            _objs = [_get_json_from_obj(o) for o in _manager.all()]
            print(json.dumps(_objs, sort_keys=True, indent=2))

        else:
            # Don't write nno JSON out to console if user wants JSON format
            print("no --id set so dumping ALL for component:{}".format(_cmp))
            pp(_manager.all())

    else:
        obj = _manager.get_by_id(_id)
        if _json:
            obj = _get_json_from_obj(obj)
            print(json.dumps(obj, sort_keys=True, indent=2))
        else:
            # Don't write nno JSON out to console if user wants JSON format
            print("Attempting to get {}://{}...".format(_cmp, _id))
            pp(obj)


def _get_json_from_obj(ob: {}):
    """
    Dumps an object out using either pretty print or JSON
    :param ob:
    :return:
    """

    if 'data' not in ob.__dict__:
        print("sorry, no 'data' in obj. Can't JSON!")
        return False
    # Otherwise, pull out the data obj as that is a dict which can be written uot as JSON
    return ob.__dict__['data']


def parse_args():

    # Root argparse
    parser = argparse.ArgumentParser(
        description='simple dumper / inspector for ToDoist',
        epilog='¯\_(ツ)_/¯',
        allow_abbrev=True)

    # What 'component'
    parser.add_argument('--component', '-c',
                        default=components[0],
                        choices=components,
                        help='The todoist component to dump'
                        )

    parser.add_argument('--id', '-i',
                        default=None,
                        type=int,
                        help='The numerical ID to dump. If not set, dumps every item of type --component'
                        )

    parser.add_argument('--do-sync', '-s',
                        action='store_true',
                        help='force ToDoist API client to sync() before dumping'
                        )

    parser.add_argument('--json', '-j',
                        action='store_true',
                        help='dump the object as JSON'
                        )

    _config_default = './config/config.yaml'
    parser.add_argument('--config-file',
                        default=_config_default,
                        type=str,
                        help='Path to TMDT config file. Defaults to {}'.format(_config_default)
                        )
    return parser.parse_args()


if __name__ == '__main__':
    # Begin by parsing any arguments from the client
    args = parse_args()

    # Assuming that nothing has blown up, we launch the tool
    launch(args)

    # And assuming that nothing there blew up, we exit
    exit(0)
