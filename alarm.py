"""One foreground alarm; standard library only. Run with --help for usage."""

import argparse
from datetime import datetime, timedelta
import re
import time
from collections.abc import Callable, Sequence


def parse_duration(value: str) -> int:
    """Accept a single positive integer and unit, bounded to 24 hours."""
    match = re.fullmatch(r"([0-9]{1,5})([smh])", value)
    if match:
        seconds = int(match[1]) * {"s": 1, "m": 60, "h": 3600}[match[2]]
        if 1 <= seconds <= 86400:
            return seconds
    raise argparse.ArgumentTypeError(
        "use a positive duration up to 24h, e.g. 30s, 10m, or 2h"
    )


def parse_clock_time(value: str) -> tuple[int, int, int]:
    """Require zero-padded 24-hour local time, with optional seconds."""
    if re.fullmatch(r"[0-9]{2}:[0-9]{2}(:[0-9]{2})?", value):
        parts = [int(part) for part in value.split(":")]
        hour, minute, second = (*parts, 0) if len(parts) == 2 else parts
        if hour < 24 and minute < 60 and second < 60:
            return hour, minute, second
    raise argparse.ArgumentTypeError("use local 24-hour time HH:MM or HH:MM:SS")


def parse_label(value: str) -> str:
    """Keep user labels on one line and reject terminal control sequences."""
    value = value.strip()
    if not value or len(value) > 120 or not value.isprintable():
        raise argparse.ArgumentTypeError("label must be 1–120 printable characters")
    return value


def next_occurrence(clock_time: tuple[int, int, int], now: datetime) -> datetime:
    hour, minute, second = clock_time
    target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def wait_until_due(
    remaining: Callable[[], float], sleep: Callable[[float], None] = time.sleep
) -> None:
    """Recheck after every bounded sleep, including early/late wakeups."""
    while (seconds := remaining()) > 0:
        sleep(min(seconds, 1.0))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set one foreground alarm. Keep this process and machine awake.",
        epilog="Examples: python3 alarm.py --in 10m | python3 alarm.py --at 07:30",
    )
    schedule = parser.add_mutually_exclusive_group(required=True)
    schedule.add_argument(
        "--in", dest="duration", type=parse_duration, metavar="DURATION",
        help="count down 1s–24h, using one unit: s, m, or h",
    )
    schedule.add_argument(
        "--at", type=parse_clock_time, metavar="HH:MM[:SS]",
        help="next occurrence of a system-local 24-hour time",
    )
    parser.add_argument("--label", type=parse_label, default="Alarm", help="alarm message")
    parser.add_argument("--silent", action="store_true", help="disable terminal bell")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    now: Callable[[], datetime] = datetime.now,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.duration is not None:
            deadline = monotonic() + args.duration
            print(
                f'Alarm in {args.duration}s: "{args.label}". Ctrl+C to cancel.',
                flush=True,
            )
            wait_until_due(lambda: deadline - monotonic(), sleep)
        else:
            target = next_occurrence(args.at, now())
            print(
                f'Alarm at {target:%Y-%m-%d %H:%M:%S} (system local time): '
                f'"{args.label}". Ctrl+C to cancel.',
                flush=True,
            )
            wait_until_due(lambda: (target - now()).total_seconds(), sleep)
        bell = "" if args.silent else "\a"
        print(f"{bell}ALARM: {args.label}", flush=True)
        return 0
    except KeyboardInterrupt:
        print("\nAlarm cancelled.", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
