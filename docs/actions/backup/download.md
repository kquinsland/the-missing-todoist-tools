# backup_download

Todoist allows all users to create a [backup](https://get.todoist.help/hc/en-us/articles/115001799989-Backups) on demand.
Additionally, premium users get a single backup per day scheduled automatically.

Backups are `zip` files containing one `csv` file per project. The `csv` file is formatted to work w/ the 
[import](https://get.todoist.help/hc/en-us/articles/208821185-Importing-Exporting-Project-Templates) functionality.


It is **STRONGLY** suggested that you begin _every_ job file with a backup action!

Does not require [Todoist Premium](../../getting-started.md#todoist-premium) 
(but it helps to have the backups automatically taken for you!)

Details are in the [`validators/backup`](../../../tdt/validators/job_file/backup/basic.py) file.

## Schema

```yaml

name: Downloads backup file by explicit date
action: backup_download
enabled: True
description: >-
  Downlands the backup file created on 2020-07-15

filters:
  - filter:
      when: "2020-07-15"
  options:
    save_location: "./backups"      
```


### Things to note:

#### Filters

Supports chaining.

Details are in the [`validators/job_file`](../../../tdt/validators/job_file/backup/basic.py) directory


- `when`: Either an explicit date in the format of `2020-07-15` for which there is a backup or a relative string for which the appropriate **past** date
 will be calculated. As future backups can't be downloaded in the present, the `tomorrow` value is not supported.
 See the [`filters/when`](../../filters/when.md) document. 
 

#### Options:
- `backup`: Path to a **directory** where the backup zip file from ToDoist will be saved.
 