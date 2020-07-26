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

See the [jobs/project/00.create.yaml](../../../jobs/v1/project/00.create.yaml) file for more.


The `action` with `name: example-project_create-filters_1` is an example of
using filters to drive the name of projects and seed each project w/ a template.

Note: the `option:delete: Yes` line means that every task that is used to generate a project name will be deleted
after the project is created.

Ultimately, the yaml below will:

- Select **every** task in your ToDoist account
- Reject **every** task that is *not* in the project called `Garage Sale 🏚️💵`
- Create a new project named after the task(s) found in the `Garage Sale 🏚️💵` project
- Position the newly created project under the `Garage Sale 🏚️💵` project
- 'seed' the new project with tasks taken from the `./templates/garage-sale.csv` file
- Delete the task from the `Garage Sale 🏚️💵` project that named the newly created project 
