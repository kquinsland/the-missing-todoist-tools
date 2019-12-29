# project_create

Projects are the core organizing mechanism for ToDoist tasks.

Does not require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/label`](../../../tdt/validators/job_file/project/create.py) file.

## Schema

Projects are created via a name and support a few additional settings.

At a minimum, each item in the `projects:` field must have:

- `from:` which identifies if the project is to be created with a specific `name` or if the project(s) will be creased
 based on search results from `filters`
 

Additionally, each project can be given a `parent` project. The display order of projects is driven by the `child_order`
field. Like with labels, projects can be  given one of a few colors.
         
### color

Color can be any integer between 30 and 49
Or one of the 19 names for the colors. Color names are in the [`tdt/defaults/colors.py`](../../../tdt/defaults/colors.py)
 file or [here](https://developer.todoist.com/sync/v8/#colors)


### Examples

See the [jobs/projecr/apply.yaml](../../../jobs/v1/project/create.yaml) file for more.



Explicitly create a project called `Some Test Project` in the root of TooDoist account w/ the color `MONA_LISA` applied
```yaml

projects:
  - from:
    name: "Some Test Project"
  color: 46
```

Create a project nested under the project `Some Test Project`

```yaml
projects:
  - from:
    name: "Some Test Child Project"
  favorite: Yes
  parent:
    # could also be specified by 'id' if known
    #id: 123456789
    project: Some Test Project
```

Use filters to drive the name of projects and seed each project w/ a template.
Note: the `option:delete: Yes` line means that every task that is used to generate a project name will be deleted
after the project is created.

Ultimately, the yaml below will:

- Select **every** task in your ToDoist account
- Reject **every** task that is *not* in the project called `Garage Sale 🏚️💵`
- Create a new project named after the task(s) found in the `Garage Sale 🏚️💵` project
- Position the newly created project under the `Garage Sale 🏚️💵` project
- 'seed' the new project with tasks taken from the `./templates/garage-sale.csv` file
- Delete the task from the `Garage Sale 🏚️💵` project that named the newly created project 

```yaml

projects:
  - from:
    filters:
      - filter:
        # The '.' character is how you say 'ANY CHARACTER' with regex, so this filter will match
        #   every task in your ToDoist account! Be VERY CAREFUL with this _especially_ when combining with the
        #   delete option!!!
          task:
            content:
              match: "."
              option:
                delete: yes

          projects:
          # But because search results are combined with the boolean AND, we can strip out all the tasks that
          #   are not in this project!
            name:
              match: 'Garage Sale 🏚️💵'

  color: ROSE
  parent:
    project: Garage Sale 🏚️💵

  template:
    file: ./templates/garage-sale.csv   
```