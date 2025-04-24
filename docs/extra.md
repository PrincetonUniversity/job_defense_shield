# Check Mode

Use the `--check` flag to see which users have recevied emails for a given alert and when they received them.
Here is an example for low CPU efficiencies:

```
$ job_defense_shield --low-cpu-efficiency --check

=====================================================================
                   LOW CPU EFFICIENCY (EMAILS SENT)                  
=====================================================================
                                                                  today
                                                                    |
                                                                    V
  u31915  _____  _____  _____  X____  _____  X____  X____  _____  __X
  u92476  _____  _X___  _____  _____  _____  _____  _____  _____  ___
  u39327  _X___  _X___  _____  ____X  _____  X____  _____  _____  ___
  u96725  _____  _____  _____  _____  _____  ____X  _____  _____  ___
  u72912  _____  X____  _____  _____  _____  _____  _____  _____  ___
  u34783  _____  _____  _____  _____  _____  _X___  _____  _____  ___
  u12458  _____  X____  _____  _____  _____  _____  _____  _____  ___
  u52797  _____  _____  _____  _____  _____  _X___  __X__  _____  ___
  u31979  _____  _____  ____X  ____X  _____  _____  _____  _____  ___
  u64118  _____  _____  X____  _____  _____  _____  _____  _____  ___
  u77201  _X___  _____  _____  _____  _____  _____  _____  _____  ___
  u65254  _X___  _____  _____  _____  _____  _____  _____  _____  ___
  u42983  __X__  __X__  __X__  _____  _____  _____  _____  _____  __X
  u36357  X____  X____  X____  _____  _____  __X__  __X__  _____  ___
  u13242  _____  _____  _____  _____  _____  _X___  _____  _____  ___
  u84230  X____  X____  _____  _____  _____  _____  _____  _____  ___
  u62968  _____  _____  _____  _____  _____  _____  _____  _____  __X
  u48309  _____  _____  _____  _____  _____  X____  _____  _____  ___
  u28569  X____  _____  _____  _____  _____  _____  _____  _____  ___
  u56129  _____  _____  _____  _____  _____  X____  _____  _____  ___

=====================================================================
Number of X: 36
Number of users: 20
Violation files: /path/to/violations/low_cpu_efficiency/
```

Time increases from left to right with today being on the far right.
Each character in each row corresponds to a day. Weekend days are blank.
An `X` character means that a user was sent an email.


The time window can be adjusted using the `--days` option:

```
$ job_defense_shield --low-cpu-efficiency --check --days=100
```
