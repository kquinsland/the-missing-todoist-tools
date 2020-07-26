# label_delete

Similar to `label_create`, except the few properties used to create a label are not supported.

Does require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/label`](../../../tdt/validators/job_file/label/delete.py) file

## Schema

The `labels:` field is a list of objects that drive the label(s) to be deleted. If you know the internal todoist ID
then you can set `from.id`. Otherwise, labels to be deleted are configured with a `filters` object.

As of now, only the `label.name` filter is supported.


### Examples

See the [jobs/label/02.delete.yaml](../../../jobs/v1/label/02.delete.yaml) file.
