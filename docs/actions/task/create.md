# task_create

Tasks are _the core_ component of ToDoist.
Does not require [Todoist Premium](../../getting-started.md#todoist-premium).

Details in the [`validators/task/create.py`](../../../tdt/validators/job_file/task/create.py) file.

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

See the [jobs/projecr/apply.yaml](../../../jobs/v1/project/create.yaml) file for more.


```yaml
##
# Showcase task_create action
##
version: 1

actions:
  - name: example-task_create_0
    action: task_create
    enabled: Yes
    description: >-
      Creates two tasks with explicit due dates

    items:
      - content: "Some September Task"
        project:
          # I happen to know that the default Inbox project on my account is `2238854217`
          id: 2238854217
        due:
          explicit:
            to: '2020-09-01T15:00:00-0700'

        # 4 is highest priority
        priority: 4

        # Don't want to see sub tasks (if any) in task list by default
        collapsed: Yes

        labels:
          name:
            - tmtdt

        # Apply my default reminder settings for this task so i don't need to use the `reminder_apply` action 
        #   later in this job file to get a reminder on the task
        auto_reminder: Yes

        # Note, the label `@tmtdt` is specified right in the task title.
        # This 'works' because `auto_parse_labels` (below) is set to yes!
        ##
      - content: "Some October Task @tmtdt"
        project:
          id: 2240560934
        due:
          explicit:
            to: '2020-10-01'

        priority: 4
        auto_reminder: Yes
        # When this option is enabled, the labels will be parsed from the task content and added to the task.
        # In case the label doesnt’t exist, a new one will be created automagically :)
        auto_parse_labels: yes

  - name: example-task_create_1
    action: task_create
    enabled: Yes
    description: >-
      Creates task with NO due date

    items:
      - content: "Some never Due Task"
        project:
          # Couch the name in ^<query>$ to make it a *literal* search for _only_ <query>
          # This only works because I have *one* project with the name `Inbox`. If I had multiple projects with 
          # the _exact same name_ then my only option would be to use the `id:` field!
          name: "^Inbox$"
        due:
          absent: Yes

        labels:
          name:
            - tmtdt

  - name: example-task_create_2
    action: task_create
    enabled: Yes
    description: >-
      Creates task with a re-occurring due date

    items:
      - content: "My Every Evening routine task @routine"
        project:
          name: "^Inbox$"
        due:
          # Note: this will be a 'floating' due date so the task will always track the local / client timezone!
          literal: "every day at 9 pm"

        labels:
          name:
            - tmtdt

  - name: example-task_create_3
    action: task_create
    enabled: Yes
    description: >-
      Creates task with a relative date

    items:
      - content: "Some Task due after tomorrow"
        project:
          name: "^Inbox$"
        due:
          # This will create a task that's due the Day of Week (DoW) that's after tomorrow. This does *not* support
          #   times. E.G.: If today is Wed, tomorrow is Thur. so the due date that is 'sent' to ToDoist
          #   will be 'Friday'.
          # Note: like the literal due date, this task will be considered floating
          relative:
             to: tomorrow
             direction: after
        labels:
          name:
            - tmtdt

  - name: example-task_create_4
    action: task_create
    enabled: Yes
    description: >-
      Creates a child task

    items:
      - content: "Some Child Task"
        project:
          name: "^Inbox$"
        due:
          # TODO: document after today and after today as a DoW
          relative:
             to: wednesday
             direction: after
        labels:
          name:
            - tmtdt

        parent_task:
          # Note: This task should already exist in the same project as the task to be created
          # TODO: test what happens when this is NOT THE CASE
          name: 'Some never Due Task'
          #id: 9999

        # The order of task. Defines the position of the task among all the tasks with the same parent_id
        child_order: 8

        section:
          # The id of the section. Set to null for tasks not belonging to a section.
          name: a2cp section

```