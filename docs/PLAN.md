# Requirements and plan — written before implementation

## Problem

Build a Python CLI alarm clock in a 30-minute exercise. The useful outcome is
that a user can schedule one alarm, see when it will fire, and receive a visible
notification without installing dependencies. AI is used for requirements,
implementation, and test generation; generated output must be reviewed.

## Acceptance criteria

- `python3 alarm.py --in 10m` fires once after ten elapsed minutes.
- `python3 alarm.py --at 07:30` schedules the next local 07:30; a past or
  exactly-equal time rolls to tomorrow. Seconds are optionally accepted.
- Exactly one scheduling option is required; malformed or zero durations fail
  immediately with a helpful message and exit status 2.
- Print the schedule immediately; flush output so it is visible in a pipe.
- On expiry print the label and request a terminal bell; `--silent` disables
  the bell. Then exit successfully. Ctrl+C cancels with status 130 and no traceback.
- No database, web UI, network, background daemon, or persisted state.

## Decisions and boundaries

- One file for application code, standard-library `argparse`, `datetime`,
  `time`, and `unittest`. Avoid packaging work for a directly runnable exercise.
- Countdown uses a monotonic deadline so wall-clock corrections cannot change
  its duration. Local clock alarms use naive system-local datetime comparisons;
  recheck wall time at least once a second and fire on `now >= target`.
- Use bounded sleeps, never a busy loop. Separate parsing, scheduling, waiting,
  and output. Inject clock/sleep callables into waiting to test without real delays.
- Strict duration grammar: a positive integer followed by `s`, `m`, or `h`.
  Limit to 24 hours to keep the use case bounded and reject huge numeric inputs.
- No snooze, recurrence, concurrent alarms, or audio-library integration in this
  scope. A visible alert is reliable; terminal sound is best effort.
- Keep the process and machine awake. No guarantee during suspend or restart.
  Explicit timezone selection and DST-gap/fold resolution are deferred; document
  local wall-clock behavior rather than claiming timezone guarantees.

## Intended 30-minute allocation (a plan, not a measured claim)

| Minutes | Deliverable |
| --- | --- |
| 0–5 | Refine scope, acceptance criteria, and tradeoffs with AI |
| 5–17 | Implement parser, deadline calculation, wait loop, alert |
| 17–25 | Test rollover, invalid input, clock changes, and cancellation |
| 25–30 | Review code, run demo, document limitations and next steps |

## Validation plan

Use deterministic fake clocks for midnight rollover, oversleep, backward wall
clock changes, and monotonic countdown behavior. Run real subprocess checks for
help, CLI errors, short expiry, and SIGINT. Review the diff for unnecessary
features and dependencies. Do not claim a recording or platform test that was
not actually performed.
