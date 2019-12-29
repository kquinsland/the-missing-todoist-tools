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

See the [jobs/project/delete.yaml](../../../jobs/v1/project/delete.yaml) file for more.


This will delete all projects that have a name matching this pattern: `Some Other $WORD Project $NUMBER`. Examples:

- `Some Other Example Project 11`
- `Some Other Testing Project 09`
- `Some Other FooBarBaz Project 972899`


```yaml
projects:
  - from:
    # Supports specific ID, if known
    # id: 2239209310
    filters:
      - filter:
        projects:
          name:
            match: 'Some Other (\w*) Project \d$'
```
