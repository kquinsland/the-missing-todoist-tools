# label_delete

Similar to `label_create`, except the few properties used to create a label are not supported.

Does require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/label`](../../../tdt/validators/job_file/label/delete.py) file

## Schema

The `labels:` field is a list of objects that drive the label(s) to be deleted. If you know the internal todoist ID
then you can set `from.id`. Otherwise, labels to be deleted are configured with a `filters` object.

As of now, only the `label.name` filter is supported.


### Examples

See the [jobs/label/delete.yaml](../../../jobs/v1/label/delete.yaml) file.

```yaml

labels:
  - from:
      # The label known as `at_work` is identified by ID 2154807380
      id: 2154807380

  - from:
      # This will delete any label that matches the regex `at_work`
      filters:
        - filter:
            labels:
              name:
                match: 'at_work'
```