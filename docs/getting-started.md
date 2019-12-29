# Getting Started

A quick and dirty guide to getting TMTDT working for you.


## Requirements

To run TMTDT, you need:

- A modern python3 environment
- A ToDoist API key (and, ideally, TooDoist Premium.)

### API Keys

ToDoist supports two different types of API keys:

- [personal API token](https://todoist.com/Users/viewPrefs?page=integrations)
- [oAuth tokens](https://developer.todoist.com/sync/v8/#oauth)

TMTDT will work with either. Personal tokens are easier to get, so that's probably the one you want. If you do go the
 oAuth route, make sure that the token has both the read _and_ write scope. TMTDT is quite useless w/o the write scope
 and is blind w/o the read scope! 

**Note**: The token will allow for _full_ read and write access to your ToDoist account. Treat the API token like you
would a password. DO NOT EXPOSE IT TO THE WORLD UNLESS YOU WANT THE WORLD TO READ/WRITE YOUR TODOIST!  

#### ToDoist Premium 

ToDoist Premium is not _required_ for TMTDT, but it certainly helps! TMTDT can manage
[labels](https://get.todoist.help/hc/en-us/articles/205195042-Labels) and 
[reminders](https://get.todoist.help/hc/en-us/articles/205348301-Reminders) but
[only for premium accounts](https://todoist.com/pricing)!

If you'd like to try out ToDoist Premium, you can [use my referral link to get 2 months free](https://todoist.com/r/k_ggsqpi).
No credit card or commit required when using that referral link. If you're happy with ToDoist premium and decide to
commit after the trial, I'll get 2 months of premium as referral credit.  Thank you in advance :) 🙏

### A note about python versions

TMTDT was developed on a mac, running Python `3.7.7`. Care was taken to make sure that file paths will be
compatible with Windows based machines, but this has not been tested / confirmed. Likewise, Python versions prior
to 3.7 are likely to work, but are not supported. As higher versions of Python 3 are released, I intend to support them
and deprecate support for older versions of python.

Additionally, a [virtual environment](https://docs.python.org/3/tutorial/venv.html) is suggested, but not required. 


## Installing

First, make sure that you have [python3](https://www.python.org/downloads/) installed. After that, the install is 
standard for a Python3 program:
  
```bash
# Make a directoory
$ cd ~
$ mkdir tmtdt
$ cd tmtdt/

# Pull down the code 
~/tmtdt $ git clone git@github.com:kquinsland/the-missing-todoist-tools.git .
Cloning into '.'...
remote: Enumerating objects: 2688, done.
    <SNIP>
Resolving deltas: 100% (1639/1639), done.

# Set up the virtual environment (optional; suggested)
~/tmtdt $ python3 -m venv ./venv
~/tmtdt $ source venv/bin/activate

# Install dependencies
(venv) ~/tmtdt $ pip3 install -r requirements.txt
Collecting todoist-python~=8.1.1 (from -r requirements.txt (line 3))
<SNIP>

# Test that the tool works
(venv) ~/tmtdt $ python3 tmtdt.py --help
usage: tmtdt.py [-h] [--version]
                [--log-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
                [--log-file LOG_FILE] [--job-file JOB_FILE]
                [--config-file CONFIG_FILE] [--dry-run] [--reset-state]

Collection of tools to automate the upkeep of ToDoist

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --log-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
                        Set log level. Defaults to INFO
  --log-file LOG_FILE   if set, the path to log to. If not set, stdout is used
  --job-file JOB_FILE   Path to the job file. Defaults to ./jobs/default.yaml
  --config-file CONFIG_FILE
                        Path to TMDT config file. Defaults to
                        ./config/config.yaml
  --dry-run             Skips over every call to commit changes back to
                        ToDoist
  --reset-state         Use to clear local todoist state and exit

Push that blue button...
```



## Using

Once installed, TMTDT needs to be configured. See below for more.
After configuration, simply create a [`job file`](readme.md#job-files) and pipe it in
to TMTDT with the `--job-file`


```bash
(venv) ~/tmtdt $ python3 tmtdt.py --job-file jobs/demo/00.setup.yaml
tmtdt.py [INFO     ] 🟩 Have '4' valid actions.
    <...SNIP...>
```

### Configure

After making a copy of the
[sample config file](../config/config.yaml.sample), use your editor of choice to fill in the correct values.


```bash
# Copy the example config file
(venv) ~/tmtdt $ cp config/config.yaml.sample config/config.yaml

# Edit the file to make it yours
(venv) ~/tmtdt $ $EDITOR config/config.yaml
```


