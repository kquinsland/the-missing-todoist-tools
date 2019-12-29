# The Missing ToDoist Tools (TMDT)

The Missing ToDoist Tools - TMDT for short - is a collection of scriptable tools designed to automate the tedious act 
of Inbox triage and general task management.


## High level feature overview:

![Screencast showing ToDoist Inbox transformed by demonstration of TMTDT](/docs/res/demo/02/combined.gif)

- Automatically create projects, labels, tasks
- 'Seed' a project from a template file
- Apply labels and projects to tasks
- Reschedule tasks with [`relative`or `explicit`](/docs/readme.md#taskdate) dates
- Set reminders on tasks
- Download ToDoist [backups](https://get.todoist.help/hc/en-us/articles/115001799989-Backups) to your computer


## Examples

![Screencast showing ToDoist Inbox transformed by demonstration of TMTDT](/docs/res/demo/01/demo.gif)

If you squint 🔍, you can see the examples below working to cleanup an Inbox.

> Apply the label `@at_work` to all tasks that:
>   - are in the `Inbox` project
>   - (and) have no label
>   - (and) end in `at work` **or** `at the office`. 
>       - Remove the `at work` or `at the office`
>       portion of the task when saving it with the labels

Or

> For every task in the `GarageSale` project:
>   - make a new project named after the task
>       - locate the new project under the `GarageSale` project
>   - 'Seed' the project with tasks from `sale-tasks.csv` file
>   - delete the original task from `#GarageSale`

And *so* much more.

If the above GIF wasn't helpful, you can see the exact `jobs`file [from the demo](/jobs/demo/01.apply.yaml).

There are several additional [example jobs](jobs/v1) based off of my original use cases that - conveniently - serve
as a guide to how I use TMTDT and complement the [documentation for each tool](/docs/actions/readme.md).

## Future Work

- [ ] Tests. I kept changing my mind about how to do most things as I re-wrote things. As such, there are no tests :(.

- [ ] More 'useful' backup and restore `action`s. As of right now, TMTDT only downloads the nightly backups that ToDoist provides for their users. There is no 'point in time' restore functionality. I have some vague ideas about how to implement this with something like [`pickle`](https://docs.python.org/3/library/pickle.html).

- [ ] Add support for searching by comment tasks.

- [ ] A web service version.

- [ ] a PIP installable version (`pip3 install tmtdt` or similar so `tmtdt.py` in installed into users `$PATH`)

- [ ] Support for multiple selectors of a given component per filter so queries can be properly bounded

- [ ] Better 'event' emitting integration. If you look deep in the code, there are a few 'pre-wired' hooks that don't do much right now. I'd like to change that so other software can be made aware of when, for example, a `job` just ran `apply_label` to some task.

### License

Take the [`GNU LGPLv3`](LICENSE.md) and add on this:

> Absolutely no commercial use for any reason without my express written consent.


### Support

Is something that I will in the time that I can afford to spare for support.
All support will be done via github issues, so please make sure you've gone through the
 [getting started](docs/getting-started.md)) guide for setup related questions and the 
 [`troubleshooting`](docs/troubleshooting/readme.md) guide for a few useful tips / tools for further debugging.
 
If, after you've confirmed a proper python3 environment *and* checked through the troubleshooting guide, search through the
[current issues](https://github.com/kquinsland/the-missing-todoist-tools/issues) before opening a new one!

Before submitting an issue, make sure you're asking a [good question](https://www.youtube.com/watch?v=53zkBvL4ZB4)
 
You can always [buy some time](https://karlquinsland.com/contact/) and have it allocated to your issue :).
 
This code is littered with `#TODO:` comments to add more polish and more. Like support, I'll get to those in my spare time.

You are *encouraged* to use the [`backup`](docs/actions/backup/download.md) action to download the most recent backup
from ToDoist before using ANY other `action`!

You are encouraged to read through the source code as it has plenty of comments which should also explain my 
thinking (the good _and_ the bad) and answer specific feature/implementation questions.

That said, pull requests are absolutely welcome. Please open an issue to discuss any significant refactor, first.
See [CONTRIBUTING](./CONTRIBUTING.md) for more.

TL;DR:

[![works badge](/docs/res/badge.svg)](https://github.com/nikku/works-on-my-machine)

Manage your expectations accordingly.
