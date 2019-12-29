# label_apply

Simply applies a series of label(s) to tasks.

Does require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/label`](../../../tdt/validators/job_file/label/apply.py) file.

## Schema

There are two fields that drive this action:

- `labels`: a list of labels to apply. Currently, specifying labels by ID is not supported. The label must already 
exist if it is to be applied. Missing labels will be skipped with a WARNING in the logs.
    
- `filters`: a list of filters that find tasks(s) to receive the labels. See the dedicated [filters](../../filters/readme.md) documentation for details

### Examples

See the [jobs/filter/apply.yaml](../../../jobs/v1/label/create.yaml) file.



```yaml


actions:
  - name: tag all tasks that mention "at work"
    action: label_apply
    enabled: True
    description: >-
      Shows how to use the filter(s) object in TMTDT w/ the labels

    labels:
      - "at_work"
      - "tmtdt"

    
    ##
    # Filters are _incredibly_ powerful. They allow for 'selection' of tasks based on certain properties.
    # The 'selections' are piped to the actual action. In this case, the tasks that match the filters
    #   below are going to get the labels configured above applied to them.
    #
    # Each filter block supports multiple selectors:
    #   task
    #     content - This is the text of the task.
    #
    #   labels
    #     name - This is the name of a label.
    #
    #   project
    #     name - This is the name of a project.
    #
    # All search strings are treated as regex expressions which can be tweaked with the `regex_options`
    #   field.
    #
    # Within a given filter block, the selectors are combined with the *AND* operator. The 'results' from each
    #   filter block are simply combined with the other blocks' results with an *OR* operator.
    #
    # After running each filter block, the action will be taken on all resulting tasks
    #
    # Additionally, some selectors support additional options that govern how the tasks that they 'originate'
    #   should be treated. The `mutate` option can be used to remove the matching part of the selector from the task.
    #
    ##
    filters:
      - filter:
          # Any task that...
          task:
            # ... ends in 'at work' or 'the office'
            content:
              match: '(at work$|at the office$)'
              option:
                # Remove the match string from the task title. Not a good idea for exact matches as the task will
                #   have an empty name set. This makes if very hard to search for the task to fix / delete it!
                mutate: Yes

          # *AND*
          # ... is in this project
          projects:
            name:
              match: 'Inbox'

          ##
          # Additionally, ignore the case
          # See: https://www.tutorialspoint.com/python/python_reg_expressions.htm
          regex_options:
            # Ignore Case
            - re.I

      - filter:
          # Any task that...
          task:
            # ... has this in their title
            content:
              match: 'at \w+ other place'
              option:
                mutate: Yes

#      - filter:
#          # Any task that...
#          task:
#            # ... is due BEFORE
#            date:
#              ##
#              # Can be *one* of:
#              ##
#              # absent: True/False - If True, tasks with No due date will be selected. "False" is an invalid value
#              #absent: Yes
#
#              # One of: 'today', 'tomorrow', 'mon' ... 'sun'
#              # Note: direction is supported, defaults to  'before'
#              # Note: user configured timezone applied
##              relative:
##                to: tomorrow
##                # due BEFORE TODAY = overdue
##                direction: before
#
#              # An explicit date/time, in Y-M-D or ISO8601 format (with no microseconds)
#              explicit:
#                #to: '2020-01-01'
#                to: '2020-08-18T14:27:00-0700'
#                # after is not inclusive
#                direction: after

#      - filter:
#          labels:
#            #absent: True
#            name:
#              match: 'hl_activity'
#              option:
#                remove: Yes

#      - filter:
#          # Any task that...
#          task:
#            # ... is due anytime/has None due date
#            date:
#              absent: Yes

```