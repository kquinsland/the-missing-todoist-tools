##
# Map each backup_* action to a specific class which generates the correct schema for that label_* action
##

action_validator_map = {
    # Downloading a backup requires minimal validation
    'download': 'Basic',
}
