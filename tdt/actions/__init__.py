# Each action that the tdt can do is implemented in it's own class, we import the *Action class here so
#   all that's needed is a from tdt.actions import * to get access to all the *Action classes
##


# This will act as a list of actions -> Classes that have been refactored :)
##
action_map = {
    # BACKUPS
    'backup_download':  'BackupDownloadAction',

    # LABEL
    'label_create': 'LabelCreateAction',
    'label_delete': 'LabelDeleteAction',
    'label_apply':  'LabelApplyAction',

    # Reminders
    'reminder_apply':  'ReminderApplyAction',

    # Projects
    'project_create':  'ProjectCreateAction',
    'project_delete':  'ProjectDeleteAction',

    # Tasks
    'task_create': 'TaskCreateAction',
    'task_delete': 'TaskDeleteAction',
    'task_reschedule': 'TaskRescheduleAction'
}
