# Check Mode

Use the `--check` flag to see which users have recevied emails for a given alert and when they received them:

```
$ python job_defense_shield.py --low-cpu-efficiency --check
```

Time increases from left to right with today being on the far right.
Each character in each row corresponds to a day. Weekends are not shown.
An `X` character means that a user was sent an email on that day.
