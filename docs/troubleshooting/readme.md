# Troubleshooting
 
There are a lot of different ways things can go wrong. Some of them are handled better than others.

Below is a non exhaustive list of simple / quick fixes that _may_ fix a problem or _may_ make it worse:


### Clear local ToDoist Cache

For performance reasons, a 'working copy' of your entire ToDoist account is kept on the same computer that runs TMTDT.
I promise that TMTDT is not 100% bug free and, in some cases, TMTDT can corrupt the local data in such a way that breaks
any attempt to sync the local date with the ToDoist servers. 

There is a `--reset-state` flag that will erase 100% of the local cache:

```bash
$ python3 tmtdt.py --reset-state --job-file jobs/demo/00.setup.yaml
2020-07-24 16:36:17,649: tmtdt.py [INFO     ] 🟩 Have '4' valid actions.
2020-07-24 16:36:17,691: cache.py [WARNING  ] Clearing local todoist cache...
2020-07-24 16:36:17,691: cache.py [WARNING  ] ...Done! Deleting '/Users/karl/.todoist-sync/'...
2020-07-24 16:36:17,692: cache.py [WARNING  ] ...Done!
2020-07-24 16:36:17,693: tmtdt.py [INFO     ] Exiting. Please re-run job...

```

### Check Release Version

TMTDT is distributed with `git`. For now, this makes it very easy to make sure you have the latest version:

```bash
(venv) ~/tmtdt $ git fetch
remote: Enumerating objects: 114, done.
    <SNIP>
Unpacking objects: 100% (87/87), 6.32 MiB | 416.00 KiB/s, done.

(venv) ~/tmtdt $ git pull
Updating 4bbb068..11c96fe
Fast-forward
    <SNIP>
(venv) ~/tmtdt$ git status
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
```

Version can also be checked with `--version`:

```bash
(venv) ~/tmtdt $ python3 tmtdt.py --version
-11c96fe-20200724
```

### debug logging

For additional insight as to how TMTDT works and where it might be going wrong, use the `--log-level DEBUG` flag to
get verbose logs. The debug level logs _and_ the job-file **are required** for support.

The `--log-file` flag may be helpful for capturing logs in a `cron` or similar environment. 

```bash

(venv) ~/tmtdt $ python3 tmtdt.py --job-file ./jobs/demo/00.setup.yaml --log-level DEBUG
2020-07-24 17:39:55,108 (DEBUG) [config.py    get_job_file:134 ]: Fetching job file: `./jobs/demo/00.setup.yaml`
2020-07-24 17:39:55,109 (DEBUG) [config.py    get_job_file:143 ]: env_var_matcher:re.compile('\\${([^}^{]+)\\}')
2020-07-24 17:39:55,109 (DEBUG) [__init__.py       read_file:17  ]: Attempting to open file:./jobs/demo/00.setup.yaml
2020-07-24 17:39:55,115 (DEBUG) [__init__.py validate_actions:43  ]: Validating root of actions block...
2020-07-24 17:39:55,116 (DEBUG) [__init__.py validate_actions:50  ]: ...Valid!
2020-07-24 17:39:55,116 (DEBUG) [__init__.py validate_actions:54  ]: Validating all '4' actions...
2020-07-24 17:39:55,116 (DEBUG) [__init__.py validate_actions:61  ]: ...validate action: 'project_create'
2020-07-24 17:39:55,116 (DEBUG) [__init__.py validate_actions:72  ]: ...loading 'tdt.validators.job_file.project' to find the class to validate action 'project_create'
    <SNIP>
```


### Inspect TooDoist Items

The [`dump.py`](../../dump.py) tool can be used to dump arbitrary objects from the ToDoist API. 

For example, dump the `label` identified by ID `2154807382`
```bash
$ python3 dump.py -c labels -i 2154807382                                                                                  480ms  Fri Jul 24 22:53:15 2020
Attempting to get labels://2154807382
Label({'color': 30,
 'id': 2154807382,
 'is_deleted': 0,
 'is_favorite': 1,
 'item_order': 4,
 'name': 'tmtdt'})

```

Or, search for the ID of the label that has `tmtdt` for a name:

```bash
 $ python3 dump.py -c labels -j | jq -r '.[] | .name, .id' | grep -A1 'tmtdt'                                               129ms  Fri Jul 24 23:28:24 2020
tmtdt
2154807382

```

