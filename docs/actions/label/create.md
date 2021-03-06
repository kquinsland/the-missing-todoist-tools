# label_create

Labels are small bits of metadata that can be applied to tasks. They are primarily identified by a string, but do support
additional properties, like [https://developer.todoist.com/sync/v8/?python#colors](colors).

Does require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/label`](../../../tdt/validators/job_file/label/apply.py) directory.

## Schema

The `labels:` field supports multiple `label` objects. 

A `label` is defined by three properties:

- `name`: string used to identify label. The only required property.
- `color`: One of a few supported colors
- `favorite`: A boolean toggle to indicate that a given label should be 'pinned' to the top of ToDoist.

### color

Color can be any integer between 30 and 49
Or one of the 19 names for the colors. Color names are in the [`tdt/defaults/colors.py`](../../../tdt/defaults/colors.py)
 file or [here](https://developer.todoist.com/sync/v8/#colors)


### Examples

See the [jobs/filter/00.create.yaml](../../../jobs/v1/label/00.create.yaml) file.
