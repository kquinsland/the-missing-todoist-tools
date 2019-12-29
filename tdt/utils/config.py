###
# helpers for parsing and validating the config from the user

# The module that does logging
import logging

# The class that configures the logging
from tdt.log_utils import LogInfo

# Basic utils/wrappers
from tdt import utils

# The actual validation for job_files
from tdt.validators import validate_actions

# And todoist config file validator
from tdt.validators.todoist_file import validate_todoist_file

from tdt.exceptions import JobFileError, TodoistFileError

# for args/cli interface
import argparse

# For path/file validation
import os

# For identifying the "use environment variables" pattern in the parsed yaml
import re

# The job files are defined as YAML
import yaml

# Debugging
from prettyprinter import pprint as pp


def validate_args(args: argparse.Namespace):
    """
    Does a few simple sanity checks on the arguments that we manage to parse

    :param args:
    :return:
    """
    log = logging.getLogger(__name__)

    ###
    # LOGGING
    ###
    # Validate that the log file, if not None, is a valid file
    if args.log_file is not None and not os.path.isfile(args.log_file):
        # The log file does not exist... see if we can create it
        try:
            with open(args.log_file, 'w+') as f:
                f.close()
        except Exception as e:
            _e = "The log file {} does not exist, and I wasn't able to make it :(. Err:{}" \
                .format(args.log_file, e)
            log.fatal(_e)
            raise AttributeError(_e)
    elif args.log_file is None:
        log.info("Logging will not be sent to a file!")

    ###
    # JOBS
    ###
    # We need to check that the jobs file we've been given is a file that we can access!
    if not hasattr(args, 'job_file'):
        _e = "Never received a mandatory argument: job_file. got:{}".format(args)
        log.fatal(_e)
        raise AttributeError(_e)

    if not os.path.isfile(args.job_file):
        _e = "Unable to access the job_file: {}".format(args.job_file)
        log.fatal(_e)
        raise FileNotFoundError(_e)

    # If nothing blew up, args are valid!
    return True


def process_config(args=argparse.Namespace):
    """
    Walks each section of the args and sets up each section of the program as needed
    :param args:
    :return:
    """
    ###
    # LOGGING
    ###
    set_logging(args)


def set_logging(args=argparse.Namespace):
    """
    Sets up logging config for the program
    :param args: the argparse args
    :return:
    """
    # LogInfo expects a Dict, we pull what we need out of args
    log_opts = {
        'log_level': args.log_level,
        'log_file': args.log_file
    }

    # Pass in the user config to LogInfo. Creation of which will configure the root logger
    LogInfo(log_opts)


def validate_job_file(job_file_path: str = ''):
    """
    Attempts to a file and, if able to read valid YAML from the file, confirm that the file defines a valid job
    :param job_file_path:
    :return:
    """

    # Open the file and pull the content.
    job_file = get_job_file(job_file_path)

    # With the YAML in hand, we need to validate it. If nothing blows up, we'll get back a list of valid objects
    #   which we'll return to the caller
    return validate_actions(job_file)


def get_job_file(job_file: str = ''):
    """
    Takes a path to a YAML file that describes a job to execute and parses the YAML into a DICT.
    Supports single environment-variables in the form of ${env_var_here:default_value_here}.
    If `env_var_here` is not defined in the current environment, the default_value_here is used

    :param job_file:
    :return:
    """
    log = logging.getLogger(__name__)
    log.debug("Fetching job file: `{}`".format(job_file))
    try:
        ##
        # This is a very clever use of add_implicit_resolver from the elastic/curator project.
        # Any string that is not native YAML, but looks like the regex ${*} will be treated as
        #   an env-var lookup.
        # See: https://pyyaml.org/wiki/PyYAMLDocumentation the Constructors, represents, resolvers section
        ##
        env_var_matcher = re.compile(r"\${([^}^{]+)\}")
        log.debug("env_var_matcher:{}".format(env_var_matcher))
        yaml.add_implicit_resolver("!env", env_var_matcher)

        # We're required to pass a function that yaml will run when it encounters an !env tag or ${} syntax
        def single_constructor(loader, node):
            # get the string that triggered the custom constructor
            value = loader.construct_scalar(node)
            # Get the string *inside* of the ${} that we'll now need to pull from env_vars
            proto = env_var_matcher.match(value).group(1)
            log.debug("Resolving '{}' via env vars...".format(proto))
            default = None
            # If there's a : in the ${thing:default} then we split on : and whatever is to the left is the env var to use
            #   and whatever is on the right is the default to use
            if len(proto.split(':')) > 1:
                envvar, default = proto.split(':')
                log.debug("user supplied default:{}".format(default))
            else:
                envvar = proto
            log.debug("envvar:{} default:{}".format(envvar, default))

            log.info("Attempting to resolve {envvar} from environment variables, falling back to: {default}"
                         .format(envvar=envvar, default=default))
            _r = os.environ[envvar] if envvar in os.environ else default
            log.debug("_R:{}".format(_r))
            return os.environ[envvar] if envvar in os.environ else default

        yaml.add_constructor('!env', single_constructor)

        # When parsing untrusted YAML, it's possible to make Python execute code. This is by design, but to
        #   prevent warning messages, and to disable support for the dangerous YAML, we specify the loader type
        # See: https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
        ##
        return yaml.load(utils.read_file(job_file), Loader=yaml.FullLoader)

    except yaml.scanner.ScannerError as err:
        # If the file could be opened, but wasn't valid YAML...
        _e = "The job_file:{} could not be parsed as YAML. Err:{}".format(job_file, err)
        log.fatal(_e)
        raise JobFileError(_e)


def get_todoist_file(todoist_file: str = ''):
    """
    Takes a path to a file and, if the file is valid yaml, returns the parsed content
    :param todoist_file:
    :return:
    """
    log = logging.getLogger(__name__)
    try:
        # When parsing untrusted YAML, it's possible to make Python execute code. This is by design, but to
        #   prevent warning messages, and to disable support for the dangerous YAML, we specify the loader type
        # See: https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
        ##
        # We pull the YAML out, then validate it
        _todo_yaml = yaml.load(utils.read_file(todoist_file), Loader=yaml.FullLoader)
        return validate_todoist_file(_todo_yaml)
    except yaml.scanner.ScannerError as err:
        # If the file could be opened, but wasn't valid YAML...
        _e = "The todoist_file: `{}` could not be parsed as YAML. Err:{}".format(todoist_file, err)
        log.fatal(_e)
        raise TodoistFileError(_e)
