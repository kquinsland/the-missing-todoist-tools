"""
root job_file validator that all others inherit from
"""
# Used to discover sub-classes of validators
import pkgutil
import importlib
# Helper to iterate through all the modules in a package w/o having to hack about w/ __all__
import os.path

# The core library that makes this all work!
from voluptuous import Required, Any, In, Length, Optional, Boolean, Schema

# Debugging
import logging
from prettyprinter import pprint as pp

# Access to the action_check_map which lists all known/possible actions
import tdt.validators.job_file


def _determine_supported_actions(_mods):
    """
    Discovers all modules inside of a package, allows you to _literally_ drop in a new validation
        file and just have it _work_
    """
    # For each module under it, if there's another package, open it up and look for the 'action_validator_map'
    _supported_actions = []
    for _m in _mods:

        # Check if it's a sub-package, that'll be a very good indicator that there's a module inside w/ a
        #   'action_validator_map' that we'll want to pull the keys() from
        ##
        if not _m.ispkg:
            continue

        # Import the module
        _mod = importlib.import_module('.{}'.format(_m.name), package='tdt.validators.job_file')

        try:
            # See if the module has a 'action_validator_map'
            _map = getattr(_mod, 'action_validator_map')
            for _act in _map.keys():
                _supported_actions.append("{}_{}".format(_m.name, _act))

        except AttributeError:
            # No worries, just pass
            pass

    return _supported_actions


class Validator:

    def __init__(self):
        # We set up a single logger in the base class
        self.log = logging.getLogger(__name__)

        # Each action that we validate will have a few properties
        ##
        # The action being validated
        self._action = ''

        # The name of the action being validated
        self._name = ''

        # The 'location' of the object being validated. Very helpful for indicating _exactly_ where the error is
        #   so the user can quickly go take a look
        ##
        self._location = ''

        # To keep things modular and dynamic, we need to load up every module inside of the job_file package
        # See:
        # https://stackoverflow.com/questions/487971/is-there-a-standard-way-to-list-names-of-python-modules-in-a-package
        ##
        # Get the location on disk of the job_file package
        _pkgpath = os.path.dirname(tdt.validators.job_file.__file__)

        # So that we can learn which modules are under it
        _mods = pkgutil.iter_modules([_pkgpath])

        # A list of ALL the supported actions
        _supported_actions = _determine_supported_actions(_mods)

        # This is the default schema that EVERY ACTION MUST HAVE no matter what the action to be taken is!
        self._schema = Schema({
            # The ACTION is required for every object! It can be any value in the list returned by all_actions()
            Required('action'): Any(
                In(_supported_actions),
                msg='action must be one of {0}'.format(_supported_actions)
            ),

            # The action must also have a name; any string with at least 1 character
            Required('name'): Any(str, Length(min=1)),

            # Description is OPTIONAL, but if present must be a string
            Optional('description', default='No description given'): Any(str),

            # Each action can have an 'enabled' field. If not present, assume enabled=True
            Optional('enabled', default=True): Boolean()
        })

        # The schema to use SPECIFICALLY for validating selectors in a filter, if supported on the action
        self._filter_selector_schema = None

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        if type(value) is not str:
            self.log.error("{} must be a string".format('Action'))
            return
        self._action = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if type(value) is not str:
            self.log.error("{} must be a string".format('Name'))
            return
        self._name = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if type(value) is not str:
            self.log.error("{} must be a string".format('Location'))
            return
        self._location = value
