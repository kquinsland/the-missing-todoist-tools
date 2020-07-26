# task_reschedule

A powerful way to alter the due-date of a task.
 

Postponing a task is just a less 'flexible' way of rescheduling a task.
Postpone does not set an arbitrary new due-date for the task, only adjusts the due-date by a given
  set of days, hours, minutes.
  
E.G: To postpone a task to 'tomorrow' you would add _exactly_ one day  to it's due date

Does not require [Todoist Premium](../../getting-started.md#todoist-premium).

Details are in the [`validators/task/reschedule`](../../../tdt/validators/job_file/task/reschedule.py) file.

## Schema

Tasks - referred to as `items` internally - support several different properties, but only the task content is required to create a task.

Each task to be created is defined in the `items:` block. At a bare minimum, the task `content` must be defined.

The *absolute* bare minimum required to create a task called "This Is A Test Task" is:

```yaml
items:
  - content: "This Is A Test Task"
```

Beyond the required `content`, you can provide several additional properties:

- `project`: Specify either the `name` or `id` of the project that the task should be created under
- `due`': Supports all of the powerful relative and explicit specifiers you've come to expect from TMTDT
- `priority`: The priority level. A number between 4 and 1 where 1 is the lowest priority and 4 is the highest
- `collapsed`: Toggles weather sub-tasks are displayed or not in task list
- `labels`: The list of labels to apply to a task. Only the labels that exist at run time will be applied.
- `auto_reminder`: Toggle weather or not the [default reminder](https://get.todoist.help/hc/en-us/articles/205348301-Reminders) will be applied to the task
- `auto_parse_labels`: Toggle weather or not ToDoist should parse out any labels with the `@label` notation from the task content. This will allow you to assign labels to a task without first having to create them!
- `parent_task`: Specify either the `name` or `id` of the task that the task should be created under
- `child_order`: number that allows for customization of sub-tasks when displayed. The higher the number, the higher it'll be in the list
- `section`: Specify either the `name` or `id` of the section that the task should be created under

#### A note about ambiguous cases

ToDoist supports multiple components with the same name. When a given property has more than one match for a given name, 
you will be required to identify the property by ID. 

For the Examples below, I have *two* projects that contain the word `Inbox`. In addition to the default 
project called `Inbox`, I created another project called `Inbox for Some Project`. 

If the `project:name` fields were left with _just_ the string `Inbox`, then both projects will match which creates an
ambiguous situation; which of the two projects should the new task be assigned? There are two ways to work around this
situation:

- use the explicit `id` for the property

- modify the regex expression to match *only* the name `Inbox` instead of all projects with a name _containing_ 
the word `Inbox`. This is done with the `^` and `$` operator. The `^` represents the beginning of a string and the `$` 
represents the end. By changing `name: Inbox` to `name: ^Inbox$`, I am changing the search from all projects with 
`Inbox` in their name to a search for all projects that have _exactly_ `Inbox` in their name 

If using the `id` to resolve an ambiguous situation, make sure that the ID is **correct**, otherwise the task
 *will not* be created and you'll get an error in the logs:
 
 ```bash
$ python3 tmtdt.py --job-file ./jobs/v1/tasks/create.yaml      
<SNIP>
action.py [ERROR    ] 🛑 Something went wrong! INTERNAL_SERVER_ERROR: Temporary error, try again later. http:500 _error_code:2
tmtdt.py [INFO     ] ☑️ DONE with action(4)://task_create (example-task_create_4)...
tmtdt.py [INFO     ] ... However, a non-fatal error did occur. ⭕
tmtdt.py [INFO     ] Execution of job://./jobs/v1/tasks/create.yaml complete. Goodbye! 👋

 ``` 

# Rather than bother with the ID, I'm going to 
 
 

### Examples

See the [jobs/task/01.reschedule.yaml](../../../jobs/v1/tasks/01.reschedule.yaml) file for more.
