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

See the [jobs/filter/01.apply.yaml](../../../jobs/v1/label/01.apply.yaml) file.
