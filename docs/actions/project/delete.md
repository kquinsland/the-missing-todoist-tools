# project_delete

Project deletion works a lot like creation. You still specify projects with an explicit `name`, `id` or with `filters` but 
the attributes used for setting color and display order are only considered when creating.   

Does not require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/project`](../../../tdt/validators/job_file/project/delete.py) file.

## Schema

Projects are deleted via a name or an ID. The name can be driven  with `filters`

At a minimum, each item in the `projects:` field must have:

- `from:` which identifies if the project is to be created with a specific `name` or if the project(s) will be creased
 based on search results from `filters`
 

### Examples

See the [jobs/project/01.delete.yaml](../../../jobs/v1/project/01.delete.yaml) file for more.
