"""
root validator class for all actions that support filters
"""
import importlib

# Debugging
import logging
from prettyprinter import pprint as pp

# Access to the action_check_map which lists all known/possible action
from tdt.validators import SchemaCheck
from tdt.validators.job_file.validator import Validator


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


class FilterValidator(Validator):

    def __init__(self):
        # After super init, we'll have working logging and a base schema
        super().__init__()

        # The schema to use SPECIFICALLY for validating selectors in a filter, if supported on the action
        self._filter_selector_schema = None

    @property
    def selector_schema(self):
        return self._filter_selector_schema

    @selector_schema.setter
    def selector_schema(self, value):

        # When the selector validator is assigned to us, we make sure that it actually has
        #   a validate attribute and that it is callable
        ##
        if type(value) is not dict:
            self.log.error("{} must be a dict".format('selector_schema'))
            return
        self._filter_selector_schema = value

    def _validate_filters(self, filters_list: list = None):
        """
        Inspects each filter object and attempts to validate
        :param filters_list: the list of filter:{} objects to validate
        :type filters_list: list
        :return:
        """

        if not isinstance(filters_list, list) or len(filters_list) < 1:
            _e = "Can't validate non-list of filters. got:{}".format(type(filters_list))
            self.log.error(_e)
            raise ValueError(_e)

        # Before we go through thee filters checking, make sure that the filter eval schema has been set!
        _e = "Can't validate filters as selector_schema is not set!"
        if self.selector_schema is None:
            raise ValueError(_e)

        # iterate through each filter object and call out for validation
        _idx = 0
        _valid_filters = []
        for _f in filters_list:
            # Add the index to the location
            _loc = "{}.filter#{}".format(self.location, _idx)
            _valid_filters.append(self._do_filter_validation(_f['filter'], location=_loc))
            _idx += 1
        return _valid_filters

    def _do_filter_validation(self, filters: dict, location: str):
        """
        :param filters: list of filter objects
        :param location: string location for messages in validation errors
        :return:
        """

        # Because the filter object is quite large and has a bit of conditional logic in it, we invite callers to
        #   validate individual filter objects using this function.
        ##
        if not isinstance(filters, dict):
            _e = "Can't validate non dict filters. got type:{} ".format(type(filters))
            raise ValueError(_e)

        # Go through each type of selector in the filter_obj, validate it against the appropriate schema
        # If we encounter any selector that we don't support, consider the filters block to be invalid
        ##
        _valid_selectors = {}
        for _selector, _selector_obj in filters.items():
            logging.debug("...validating selector of type '{}' with data:\n{}".format(_selector, _selector_obj))

            if _selector not in self.selector_schema.keys():
                _e = "Selector '{}' from filter block in {} is not one of the supported selectors: {} " \
                    .format(_selector, location, list(self.selector_schema.keys()))
                raise ValueError(_e)

            # Otherwise, load up the correct schema and update the location string
            _s = self.selector_schema[_selector]
            _l = "{}.selector:{}".format(location, _selector)

            # If not valid, exceptions will bubble up. Otherwise, append and move on to the next!
            _valid_selectors[_selector] = SchemaCheck(_selector_obj, _s, _l).result()

        # We have made sure that every selector in the filter object is valid, but now we must confirm that
        #   we have at least one selector. That is, we must make sure that the user didn't specify a filter object
        #   that has ONLY the regex_options key!
        ##
        # Make sure that the list of valid selectors is more than just the optional 'regex_options'
        if 'regex_options' in _valid_selectors.keys() and len(_valid_selectors) == 1:
            _e = "Filter block in {} is invalid, at least one selector besides '{}' must be present" \
                .format(location, 'regex_options')
            raise ValueError(_e)

        # Otherwise, the validated selectors are good to return!
        return _valid_selectors
