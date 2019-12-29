###
# The collection of actions that can be taken on "label" resources
##

# Inherit from...
import re

from tdt.actions.action import Action
from tdt.actions.utils import get_components_by_name_with_regex

# Debugging
from prettyprinter import pprint as pp


class LabelAction(Action):

    def __init__(self):
        """
        LabelAction is base for all the label* things. Wraps SUPER() and holds all properties common to label* actions
        """
        super().__init__()

        self.component = 'labels'

        # The actual backing store for the components the user gives us
        ##
        # List of raw Labels objects user gives us to work with
        self._component_objs = {}

        # List of labels from user mapped to their IDs
        self._component_ids = {}

        # All the tasks we get from filters
        self._matching_tasks = []

    @Action.components.setter
    def components(self, value: list):
        """
        User will give us either a simple list of strings or a more complicated labels object. We sort through
            both and munge into a common format
        :param value:
        :return:
        """
        if not isinstance(value, list) or len(value) < 1:
            _e = "Need at least one valid {}. got:{}".format(self.component, value)
            self.log.error(_e)
            raise ValueError(_e)

        # We'll re-arrange the data into a format that's easier to work with
        # Note: the format of 'value' will be DIFFERENT if creating or deleting/applying
        for o in value:
            # The only time 'value' will be more than a list of strings is when the user wants to create
            #   a label as creation implies optional settings. As we iterate through value, if all we have is strings
            #   then we're in the simple case
            ##
            if isinstance(o, str):
                self._component_objs[o] = {}
                continue

            # Otherwise, we're in a more complicated case which requires a bit of munging...
            # Pull out the label from the object, we'll use this as the key when storing
            _lbl_name = o.pop('label')

            # Store
            self._component_objs[_lbl_name] = o

        # Now that we've stored the user given label objects in a helpful format, we'll want to check if any of the
        #   labels exist already.
        ##
        self.log.debug("Checking {} {} for pre-existence... ".format(len(self._component_objs.keys()), self.component))

        for _lbl in self._component_objs:
            self.log.debug("fetching ID for {}://{}...".format(self.component, _lbl))
            # Pull out the labels.match into a regex query, because the user is providing *only* a string
            #   we have no regex flags
            ##
            _labels_title_re = re.compile(_lbl, flags=0)

            # Run the filter to get the labels
            _labels = get_components_by_name_with_regex(self.api_client, self.component, _labels_title_re)

            # If we got 1 result, then we know the label exists already and should not be re-created. If the user
            #   wishes to modify the existing label, they need a different action block or to delete the label and
            #   let this action block re-create it
            ##
            if len(_labels) == 0:
                # the label does NOT exist, so we'll create it!
                self.log.debug("... unable to. {}://{} needs creation!".format(self.component, _lbl))
                continue
            else:
                #  Otherwise, we should have something we can store :)
                self.log.debug("... found {}://{} ".format(self.component, _lbl))
                self._component_ids.update( {_x['name']: _x['id'] for _x in _labels})

