# reminder_apply

Does require [Todoist Premium](../../getting-started.md#todoist-premium).

Todoist supports two classes of reminders for every task:

- date/time 📆 ⌚
 - explicit: an exact date/time
 - relative: some number of minutes from now / before task due
- location 🗺️


Reminders can be distributed to clients via:

- e-mail 📧
- mobile text message 📟
- mobile push notification 📲

Details are in the [`validators/reminder`](../../../tdt/validators/job_file/reminder/filtered.py) file.


## Schema

In addition to the basic schema that defines every job, there are two core components that need to be filled out with
the `reminder_apply` action: 

- `filters`: The tasks to apply reminders to
- `reminders`: Define the reminder(s) to apply to the tasks from `filters`


### reminders

Accepts multiple reminders. Each reminder will be applied to each task surfaced by `filters`.

Every reminder must be identified by a `type` and a `service`. 

Supported `type`s:

- `absolute`
- `relative`
- `location`

Supported `service`s:
 
- `default`: user's default settings.
- `email`: email...
- `mobile`: for text message.
- `push`: for mobile push notification.
 

#### Absolute

The simplest of time based reminders. Just specify a `when` field.
The `when` field must be a valid [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) formatted string ending in _either_
 `Z` to indicate [ZULU time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time) **OR** with a valid timezone offset. 

Example:
```yaml
- type: absolute
  service: default
  when: "2020-06-16T15:59:00-07:00" # could also be written as "2020-06-16T08:59:00Z"
```


#### Relative

Of the two time based reminders, the more flexible one. Simply supply any positive number for the `minutes` field.

Note: The reminder will **not** be added to a given task if the reminder would occur in the past. Example: If a task is 
due today at 1PM and a reminder with  `minutes: 5` is set, then the `joob` containing the `reminder_apply` action 
*MUST* be run _before_ 12:55PM if the reminder is to be set. Running the `job` at 12:58PM would mean that the task is due
in 2 minutes and therefore can't have a reminder 5 minutes before its due!


```yaml
- type: relative
  service: default
  minutes: 7 # Will fire off a reminder 7 min before task is due
```

#### Location

Rather than a single time-based field, the `where` block must be set.

- `name`: Human friendly 'alias' for the lat/long pair
- `latitude`: Self explanatory
- `longitude`: Self explanatory
- `trigger`: one of `on_enter` or `on_leave`
- `radius`: optional radius, in meters

```yaml
- type: location
  service: push
  where:
    name: Hacker Lab
    latitude: 38.566112
    longitude: -121.475908
    trigger: on_enter
    radius: 20
```
 
### Filters

Supports chaining.

Supports filters of type:

- `items` (tasks)
- `labels` 

Only the `mutate` field is supported `option`.


### Examples

See the [jobs/filter/apply.yaml](../../../jobs/v1/reminder/apply.yml) file.