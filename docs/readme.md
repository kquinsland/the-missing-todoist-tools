# Overview of TMTDT

Each 'tool' in TMTDT is exposed as an `action`.
A `job file` composes one or more `action`s.

Every `action` has additional tweaks and settings that can be applied.
Specific details are in the [documentation for each `action`](actions).


## Filters

Filters are _incredibly_ powerful. They allow for 'selection' of 'components' - like, tasks, for example - based on
certain properties. Effectively, they build a search query which can select various components
(tasks, projects, labels...etc) from your ToDoist account.

Ultimately, the complete set of 'matching' components is passed on to the `action` which allows for expressions
equivalent to:
 
 
> Delete all labels that are either `at_work` or contain `some_*_at_work`

and

> Delete all projects that begin with `idea:` and end with `2018`

and

> Create a project for every task in the `#GroupEffort` project and without the `@dont_tmdt` label

... etc.
 
 
The 'garage sale' demo from the [readme](../readme.md) demonstrates the use of filters to build projects. 
 
Some filters operate on dates, some as simple yes/no toggles and others use regex which can make them
 **incredibly** powerful.

The results of each search and be combined with the boolean `AND`, `OR` operators as needed. 

The action to be used with the filters determines which component is used. Not all actions support all filters.

For example, when using `filters`:
 - in the `label_apply`_ action, the tasks that match the filters will get labels.
 - in the `project_delete` action, the projects that match the filters will get deleted.
 


### Component Selectors

As of now, there are three major `components` that have some `properties` that can be `selected` on.


- Items: Under the hood, ToDoist refers to individual tasks as 'items'.
  - content: search through the title of a given task. Supports regex.
  - date: several different ways to search by task due date. See [dates](#markdown-header-dates) for more

- Labels
  - name: Identical to `Items.content` but for labels. Supports regex.
  - absent: toggle to apply to tasks that have NO label. Use regex to build a [NOT AND](https://stackoverflow.com/questions/7548787/regex-for-and-not-operation) query if you must.

- Projects
  - name: Identical to `Items.content` but for projects. Supports regex.


You can combine multiple `components` in a given filter, but each `filter` object can have *one* of 
the `property.selector` for each `component` type. This means that multiple `selector`s within a 
given `component` are not currently supported. 

Each `component` within the `filter` block is combined with a boolean `AND`. 

The results of each filter are combined into a final set with the boolean `OR` operation.


#### Options

In some cases, the individual `property.selector` can support additional options which will change how the `component` 
that the `selector` originated should be treated when the `action` is performed. 
As of now, there are only two supported options: 

- `mutate`: Will 'mutate' the originating component's name. E.G.: remove the matching portions from the name. This is
    the option that transformed the demo task `Ask boss about a raise at work` to `Ask boss about a raise @at_work` 
- `delete`: Will 'delete' the originating component! This is the option that caused the original tasks under 
    the `Garage Sale` project from the demo to be deleted.

Both `mutation` and `deletion` may not be supported for a given `action`. E.G.: 
    `Create a new project for every project that has 'Example' in it's name, delete originating project` makes no sense; 
    it would simply create a nwe project named 'Example' and then delete the first project named 'Example'. 🤷

Obviously, exercise caution when using the `delete` option. Also, be mindful of the `mutate` option when using a regex
query for a full and exact match. If you're not careful, the `component` will be updated to have an empty name!
This makes if very hard to search for the component to fix / delete it! 

Additionally, each filter has a `regex_options` object which can be used to pass in supported
[flags](https://docs.python.org/3/library/re.html#re.A) to tweak the behavior of your regex queries. This option applies
to the _whole filter_ unlike the per-selector options `mutate` and `delete`


### task.content


```yaml
    - filter:
        task:
            content:
                # 'select' any task that ends in `at work` or `at the office`
                match: '(at work$|at the office$)'
                option:
                    mutate: Yes
```


### task.date

Note, only *one* of `absent`, `relative`, `explicit` can be used at a time!

```yaml
    - filter:
        task:
            date:
                absent: Yes # Or no, false...

                # One of: 'today', 'tomorrow', 'mon' ... 'sun'
                # Note: direction is supported, defaults to  'before'
                # Note: user configured timezone applied
                relative:
                    to: tomorrow
                    # due BEFORE TODAY = overdue
                    direction: before

                # An explicit date/time, in Y-M-D or ISO8601 format (with no microseconds)
                explicit:
                    #to: '2020-01-01'
                    to: '2020-08-18T14:27:00-0700'
                    # after is not inclusive
                    direction: after
```


### labels.name

```yaml
    - filter:
        labels:
            name:
                match: 'work_activity'
                option:
                    delete: Yes
```

### projects.name

```yaml
    - filter:
        projects:
            name:
                match: 'Inbox'

```


## Job Files

Each job file **must** have a `version` identifier and a single `actions:` block at it's root.

```yaml
##
# Example job file

version: 1

actions:
  - action: ...

```

### Actions


Each action object **MUST** have:
- `name:` a unique name for each action
- `action:` the specific action to take

Each action object **SHOULD** have:
- `description:` A free-form field mainly for additional documentation
- `enabled:` a simple flag for easily skipping a given action in a chain

Including the optional fields, the BARE MINIMUM for an action block looks like this:

```yaml
##
# Simple job file with one action: reminder_apply
##
version: 1

actions:
  - name: apply a geospatial reminder for tasks that i need to do at the office
    action: reminder_apply
    enabled: Yes
    description: >-
      remind me about all the tasks with the @at_office label when I get to the office


    # How/When/Where are we reminding:
    # See: https://developer.todoist.com/sync/v8/?python#add-a-reminder
    reminders:
        # Supported: relative, absolute, location
      - type: location
          ....
```
