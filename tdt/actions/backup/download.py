##
# Code that downloads a backup file
##


# Inherit from...
import datetime

from tdt.actions.backup import BackupAction
from tdt.actions.utils import *

# Fabulous date/time parser tool
import dateutil.parser

# Debugging
from prettyprinter import pprint as pp

# Requests Lib for the HTTP download
import requests


class BackupDownloadAction(BackupAction):

    def __init__(self):
        super().__init__()
        # After calling the super() we'll have a log object that we can use to announce to the world that we're alive!
        self.log.debug("BackupDownloadAction")

        # We'll get a list of datetime objects that represent the date of each backup file that we need to download
        self._dates = []

        # List of the URL(s) that we can get backups from
        self._urls = []

    def do_work(self, action_params: dict):
        """
        Does the work of LabelCreateAction
        :param action_params:
        :return:
        """

        # Caller is going to give us a list of filters that will have been parsed into datetime objects.
        # We'll go through each of the datetime objects and 'downsample' to just date
        ##
        for f in action_params['filters']:
            _when = f['filter']['when']
            if isinstance(_when, datetime):
                _when = _when.date()

            # Otherwise, it'll already just be a date obj which needs no replacement
            self._dates.append(_when)

        # After 'down converting' the user given filters, we need to group ToDoist Backups by date. Allow me to explain.
        #
        # Todoist stores the date and time of the backup as the 'version'. This means that it is possible to have
        #   multiple backups for a given day. However, we've already cast any datetime from the user to just date().
        #
        # In the (unlikely?!) event that there's more than one backup for a given day, it will be impossible to know
        #   which one we should download. E.G.: User told us to download the backup for "today", but, in addition
        #   to the automatic backups created nightly by ToDoist, the user created two manual backups. In total,
        #   there are three backups, each with the same date (today), but all three have different times associated
        #   with them: 1 AM, 9AM and 2PM. This means that there are three different 'versions' for today.
        #
        # The solution is to download the *most recent* backup for a given day. In the example above, the backup
        #   from 1AM and 9AM won't be downloaded, only the one at 2PM.
        ##
        self.log.debug("grouping todoist backup versions by date...")
        _backup_by_date = self._get_most_recent_backup_by_date()

        # Now that we have a list of all dates that a backup took place on, see if any of the dates match with dates
        #   the user told us they want a backup for...
        ##
        for _d in _backup_by_date:
            if _d in self._dates:
                self.log.info("...will fetch backup for {}.".format(_d))
                # We store the url and the date
                self._urls.append(
                    {
                        'd': _d,
                        'u': _backup_by_date[_d]
                    }
                )

        # Now, fetch all the backups that we can, alert the user if none
        if len(self._urls) < 1:
            _w = "No backups found! Could not find a backup file for any of the date(s):{}".format(self._dates)
            self.log.warning(_w)
            return False

        self.log.info("Fetching backups for {} dates...".format(len(self._urls)))

        for _obj in self._urls:
            # get the URL and Date out
            _url = _obj['u']
            _d = _obj['d']
            ##
            # We have a URL that should get us a file. Take the file name out of the URL and combine w/ the
            #   users desired save location to create a full file path
            ##
            # We know that the URL will have a filename.extension in it, so split on the . and take the last token
            #   to be the file extension.
            _ext = _url.split('.')
            _ext = _ext[len(_ext)-1]
            _fname = "{}/{}.{}".format(action_params['options']['save_location'], _d, _ext)
            self._download_backup_to_file(_url, _fname)
            self._emit_event('backup_download', _url)

        return True

    def _download_backup_to_file(self, url: str = '', where: str = ''):
        """
        Downloads the backup from URL and saves to File
        :param url:
        :return:
        """

        # ToDoist has the backup files behind authentication... even though there's a ?token=X in the URL for each
        #   backup URL...

        _h = {
            'Authorization': "Bearer {}".format(self.api_token)
        }

        if self.dry_run:
            self.log.info("Was about to download the file {} and save to {}... but --dry-run means this is far as i go!"
                          .format(url, where))
            return

        # Ask for the file; tell req. lib that we'll expect the payload to be streamed back (like a file would be...)
        r = requests.get(url, headers=_h, stream=True)

        # If anything went wrong, be vocal about it
        r.raise_for_status()

        # But if nothing went wrong, then we save the file :)
        with open(where, 'wb') as fh:
            for block in r.iter_content(1024):
                fh.write(block)

        return True

    def _group_backups_by_date(self):
        """
        Groups backup 'versions' by date
        :return:
        """
        _backups = {}

        # Get all the backups that todoist has for the account
        for _b in self.api_client.backups.get():
            # Get the date+time of the current backup, cast down to just the date
            _v = dateutil.parser.parse(_b['version'])
            _d = _v.date()
            if _d not in _backups:
                _backups[_d] = {}
            _backups[_d].update({_v: _b['url']})
        return _backups

    def _get_most_recent_backup_by_date(self):
        """
        Identifies the most recent backup for a given date
        :return:
        """
        # Get all backups, indexed by date
        _backups_by_date = self._group_backups_by_date()

        # Now that we have a list of all dates that a backup took place on find the most _recent_ backup for that date
        ##
        _most_recent_backup_by_date = {}
        for _date in _backups_by_date:
            _backups = _backups_by_date[_date]
            self.log.debug("have {} backups for {}...".format(len(_backups), _date))

            # _backups will be a list of DICTs which cant easily be sorted. We'll have to do it ourselves
            _recent = None
            for _date in _backups:
                if _recent is not None:
                    # more recent, more bigger
                    if _date > _recent:
                        _recent = _date
                else:
                    _recent = _date
            # Now that we know the most recent backup on this date, store the URL and Date
            _most_recent_backup_by_date[_recent.date()] = _backups[_recent]
        return _most_recent_backup_by_date
