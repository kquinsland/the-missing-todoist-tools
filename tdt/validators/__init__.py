# We take advantage of the voluptuous schema validator library for python.
# The SchemaCheck class wraps voluptuous.
##
import importlib

from voluptuous import Schema, Required

from tdt import TDTException
from tdt.validators.schemacheck import SchemaCheck

# So we can log
import logging
log = logging.getLogger(__name__)


# See: https://strftime.org/
# ISO w/ TZ: 2020-03-20T14:32:16+13:00
iso_8601_fmt = '%Y-%m-%dT%H:%M:%S%z'


# At the root level, there MUST be a field called actions that points to a list
root_schema = Schema(
    {
        # As of right now, only version 1 of actions file is supported
        Required('version'): 1,
        Required('actions'): list
    }
)


# Validation is a tad complex so we break it up into several classes inside modules. This function is the
#   entry-point that is called to validate the parsed actions
def validate_actions(data: dict):
    """
    Takes a parsed dict of actions and dynamically loads the correct validator class from the right module
    :param data:
    :return:
    """

    # Caller will pass a parsed - but not validated - dict. There is some basic validation that we can do before we
    #   need to inspect each action block.
    ##
    log.debug("Validating root of actions block...")

    valid_root = SchemaCheck(data, root_schema, 'Actions File').result()
    if not valid_root:
        _e = "Job File '{}' appears invalid. Can't continue!".format('root')
        # TODO: make a specific TDT exception
        raise TDTException(_e)
    log.debug("...Valid!")

    # We have a valid root, we can now move on to validating each of the actions
    actions = data['actions']
    log.debug("Validating all '{}' actions...".format(len(actions)))

    # We'll append the validated actions here
    validated_actions = []

    for action_block in actions:
        action = action_block['action']
        log.debug("...validate action: '{}'".format(action))

        # Based on the action, which module/class do we load?
        # Cut the action into the module and class
        _action_tokens = action.split("_")
        _super_validator_mod_name = 'tdt.validators.job_file.{}'.format(_action_tokens[0])

        # After splitting the action name/class of action, we're left w/ a specific type oof action
        _action_type = _action_tokens[1]

        # Load the module and pull out the mod-specific validator map
        log.debug("...loading '{}' to find the class to validate action '{}'".format(_super_validator_mod_name, action))

        try:
            # Load the 'super' module which will contain the map of all label_* actions and the class that validates
            #   them
            ##
            _super_validator_mod = importlib.import_module(_super_validator_mod_name)
            log.debug("_super_validator_mod:{}".format(_super_validator_mod))

            _action_validator_map = getattr(_super_validator_mod, 'action_validator_map')
            log.debug("_action_validator_map:\n{}".format(_action_validator_map))

            # Look up which class to use for validation
            if _action_type not in _action_validator_map:
                _e = "Unable to find a class for validating _action_type '{}'. _action_validator_map:{}".format(
                    _action_type, _action_validator_map)
                log.error(_e)
                raise TDTException(_e)

            # Otherwise, we now know which class to load from the module
            _validator_class_name = _action_validator_map[_action_type]

            # Add the validator class name to the super mod name to get the full path to the module we'll want to
            #   load the class from
            ##
            _validator_mod_name = '{}.{}'.format(_super_validator_mod_name, _validator_class_name.lower())
            _validator_mod = importlib.import_module(_validator_mod_name)

            # We now know which package, module, class too load :)
            log.debug("...validating '{}' with '{}.{}'".format(action, _validator_mod, _validator_class_name))
            _validator_class = getattr(_validator_mod, _validator_class_name)

            # Make instance of class
            validator = _validator_class()

            # Do the Validation, we'll get a fully parsed/coerced object back *or* an exception
            validated_actions.append(validator.validate(action_block))

        # Blow up if the module couldn't be found
        except ModuleNotFoundError as mnfe:
            _e = "Unable to validate the action '{}' as no module found. mnfe:{} ".format(action, mnfe)
            log.error(_e)
            raise TDTException(_e)

    # Assuming nothing blew up during validation, return everything that we validated/parsed
    return validated_actions
