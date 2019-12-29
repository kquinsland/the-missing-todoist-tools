"""
Creates Labels from a given ToDoist account.

"""
from tdt.actions.label import LabelAction


# Debugging
from prettyprinter import pprint as pp


class LabelCreateAction(LabelAction):

    def __init__(self):
        super().__init__()

        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("LabelCreateAction!")

        self.action = 'create'

    def do_work(self, action_params: dict):
        """
        Does the work of LabelCreateAction
        :param action_params:
        :return:
        """

        # set labels; triggers fetch of label_ids as well as a validation measure
        self.components = action_params['labels']

        # We'll now have a list of all the _known_ labels and their IDs. Iterate through the full list of labels
        #   that thee caller gave us and find the labels that are _missing_. Those are the ones that we'll need to
        #   create
        ##
        _existing = []
        _new = []

        # See which of the labels we were able to resolve into IDs
        for _lbl_name, _lbl_obj in self.components.items():
            if _lbl_name in self._component_ids.keys():
                _existing.append(_lbl_name)
            else:
                _new.append(_lbl_name)

        if len(_existing) > 0:
            self.log.warning("⚠️ Of the {} labels to create, {} already exist...".format(
                len(action_params['labels']), len(_existing)))

        if len(_new) < 1:
            self.log.warning("⚠️ ...No new labels to create!")
            return

        self.log.info("Creating {} new labels...".format(len(_new)))

        for _l in _new:
            # The _lbl does not have a matching ID... so that's our queue to create it!
            self.log.debug("There is no matching ID for label:{}. Creating...".format(_l))

            # Fetch the label object, see if there's color and favorite properties
            _lbl_obj = self._component_objs[_l]

            # Color and favorite
            _c = False
            _f = False

            if 'color' in _lbl_obj:
                _c = _lbl_obj['color']

            if 'favorite' in _lbl_obj:
                _f = _lbl_obj['favorite']

            # Note: is_favorite needs a 1 or 0, not True, False :/
            _r = self.api_client.labels.add(name=_l, color=_c, is_favorite=int(_f))
            self._emit_event('label_create', _r)

        return self._commit_changes()
