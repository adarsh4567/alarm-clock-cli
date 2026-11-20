# Candidate recording guide

The assignment asks for a narrated recording of the build process. A later
walkthrough cannot truthfully replace that. This repository was prepared with
AI assistance; do not describe generated code as independently written or a
reconstruction as the original recording.

If recording now, disclose that this is a fresh rebuild using the prepared
plan. Confirm with the recruiter if a rebuild is acceptable. Use your own voice
and make decisions you can explain under follow-up questions.

## Prepare

1. Open a terminal, editor, and the AI conversation. Hide unrelated tabs and
   personal notifications. Start a screen recorder with microphone enabled.
2. Test a short recording for legible code and audible narration.
3. In a separate working directory, start from the initial planning commit
   shown by `git log --reverse --oneline`. Do not overwrite the finished branch.

## Suggested 30-minute fresh rebuild

| Time | Show and discuss |
| --- | --- |
| 0–5 min | Ask AI to critique the requirements and plan before implementing. Explain single-alarm scope and what is deferred. |
| 5–17 min | Build the CLI with AI assistance. Inspect generated code before accepting it. Explain monotonic versus wall time and tomorrow rollover. |
| 17–25 min | Add and run tests. Explain why fake clocks matter; demonstrate invalid input, short expiry, and Ctrl+C. |
| 25–30 min | Review the diff and README. Identify an actual issue or limitation and discuss its impact. Show final test results. |

## Useful prompts to use, adapt, and discuss

- “For a 30-minute standard-library Python CLI alarm, critique this scope and
  list acceptance criteria and ambiguous time behavior before writing code.”
- “Implement only the accepted scope. Keep time sources injectable and avoid
  threads. Explain the trigger condition and why each clock is appropriate.”
- “Review this implementation for midnight rollover, clock adjustments,
  invalid input, terminal behavior, and cancellation. Suggest focused tests.”

## Demo commands

```sh
python3 alarm.py --help
python3 alarm.py --in 3s --label "Recording demo"
python3 alarm.py --in 0s
python3 alarm.py --in 1h
# Press Ctrl+C after the schedule line appears.
python3 -m unittest discover -s tests -v
git diff
```

Explain that terminal sound can be muted and that the process must stay alive.
Before sending, check the recording link in a private/incognito window so the
reviewer can access it. Keep the CV out of the public source repository.
