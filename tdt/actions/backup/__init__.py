###
# Base for all Download_* actions
##

from tdt.actions.action import Action


class BackupAction(Action):

    def __init__(self):
        """
        Backup Action is base for all the backup* things.
        Wraps SUPER()
        """
        super().__init__()
        self.log.debug("BackupAction")
