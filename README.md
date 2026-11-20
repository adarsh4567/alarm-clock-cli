# Python CLI Alarm Clock

A small foreground alarm clock built with Python's standard library. Schedule
one countdown or the next occurrence of a local clock time. No installation,
database, network access, or UI framework required.

## Run

Requires Python 3.10 or newer. From this repository:

```sh
python3 alarm.py --in 10m --label "Take a break"
python3 alarm.py --at 07:30 --label "Wake up"
python3 alarm.py --at 14:05:30 --silent
python3 alarm.py --help
```

On Windows, use `py` instead of `python3` if needed.

For a quick demo:

```sh
python3 alarm.py --in 3s --label "Demo"
```

```text
Alarm in 3s: "Demo". Ctrl+C to cancel.
ALARM: Demo
```

The schedule prints immediately. At expiry, the application prints the alarm
label, emits a terminal bell unless `--silent` is set, and exits. Sound depends
on your terminal settings; the text alert is always printed. Press Ctrl+C to
cancel while waiting.

## Behavior

| Input or event | Result |
| --- | --- |
| `--in 30s`, `--in 10m`, `--in 2h` | Countdown using one positive integer and one unit |
| Countdown outside 1 second–24 hours | Usage error |
| `--at HH:MM` or `--at HH:MM:SS` | Next system-local occurrence; seconds default to zero |
| Time already passed or exactly equal to current time | Tomorrow |
| Both scheduling flags, or neither | Usage error |
| Label | 1–120 printable characters, with surrounding whitespace removed |
| Expiry | One alert; exit 0 |
| Invalid arguments | Helpful error on stderr; exit 2 |
| Ctrl+C during the alarm | Cancellation message; exit 130 |

## Engineering decisions

The initial [requirements and plan](docs/PLAN.md) were written and committed
before application code. The 30-minute allocation there is a proposed budget,
not a claim about measured completion time.

- **Narrow scope:** one alarm per process. Recurrence, snooze, persistent state,
  and background services add lifecycle and interaction complexity beyond this
  exercise. Multiple independent terminal invocations are possible.
- **Two clock semantics:** countdowns use `time.monotonic()` so changing the
  system clock cannot shorten or lengthen the requested interval. Clock-time
  alarms recheck local wall time so a manual clock adjustment affects them.
- **No equality-only trigger:** expiry uses `remaining <= 0`. Oversleeping or a
  forward clock jump still triggers once rather than missing the alarm.
- **Bounded waiting:** sleeps last at most one second, avoiding a busy loop and
  allowing clock-time alarms to notice adjustments. OS scheduling may delay
  delivery; this is not a real-time scheduler.
- **Testable core:** parsing and date calculations are separate functions.
  Injected clocks and sleep make timing behavior deterministic in tests, without
  threads, patched global time, or real-minute waits.
- **Portable notification:** visible stdout plus a best-effort terminal bell.
  No platform-specific audio dependency or shell command execution.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The suite tests invalid input, boundary values, calendar rollover, early and
late wakeups, clock adjustments, silent output, one-shot expiry, and
cancellation. It includes real subprocess checks for CLI behavior, a one-second
alarm, and POSIX SIGINT. The POSIX signal check is skipped on Windows; injected
interrupt checks still exercise both scheduling modes there.

See [validation and review](docs/REVIEW.md) for the environment actually tested.
CI runs the same suite on Linux, macOS, and Windows; a configured workflow is
not itself evidence of a successful run.

## Limitations and possible next steps

Keep the terminal process running and the machine awake. Closing it or restarting
the machine loses the alarm. Suspend behavior of the monotonic clock varies by
platform, so countdowns do not promise to include time spent asleep.

Clock alarms use the machine's local wall time. They do not resolve DST gaps or
folds explicitly: a skipped time fires when the clock advances past the target;
a repeated time can match its first occurrence. A backward correction can delay
the alarm. Timezone changes during waiting are also outside the supported use
case. Add an explicit timezone and a documented DST policy before expanding to
timezone-sensitive daily alarms.

With more time, the first improvement would be a repeat-until-dismissed alert
with snooze, followed by explicit timezone/DST handling. Persistence and a
background service would require a separate product decision.

## AI-assisted process

AI helped refine requirements, choose the design, implement code, and generate
tests. The working session ran the tests and reviewed generated output for
clock semantics, parsing, scope, and notification limits. See the plan and
review documents for the decision record.

No screen recording is included or claimed. [The recording guide](docs/RECORDING.md)
helps the candidate record their own narrated process and disclose AI assistance.
