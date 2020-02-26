# Process CPU affinity tuner

This is a simple interactive tool to tune process CPU affinity.
Internally it uses `taskset` to change CPU affinity. Features include:

* It allows users to select interested processes
* It can tune affinity of threads in side processes
* It's interactive.

Example session:

```
$ affinity-tuner 
cmd: help
Available commands:
  bind       Bind a process to a few cpus.
  exit       Exit the program.
  help       Show usage.
  pgrep      Search for processes with given key words
  ps         Print all currently running processes
  quit       Exit the program.
  reset      Reset selection.
  select     Add processes to selection.
  threads    Print threads in processes.
cmd: pgrep quick
PID    AFNT CMD
9587   1111 quick-note
cmd: select 9587
PID    AFNT CMD
9587   1111 quick-note
cmd: threads
PID    AFNT CMD
9587   1111 quick-note
9588   1111 QXcbEventReader
9589   1111 QDBusConnection
9590   1111 gmain
9591   1111 gdbus
9593   1111 quick-n:disk$0
cmd: bind 9590 2
pid 9590's current affinity list: 0-3
pid 9590's new affinity list: 2
cmd: threads
PID    AFNT CMD
9587   1111 quick-note
9588   1111 QXcbEventReader
9589   1111 QDBusConnection
9590   0100 gmain
9591   1111 gdbus
9593   1111 quick-n:disk$0

```

In this example, I selected process `quick-note`, and changed the CPU binding of thread `gmain`.
Originally the thread `gmain` can run on all CPU cores, this program changes it to run on CPU 2 only.

