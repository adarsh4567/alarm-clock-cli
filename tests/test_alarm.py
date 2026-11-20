import argparse
from contextlib import redirect_stdout
from datetime import datetime, timedelta
import io
from pathlib import Path
import signal
import subprocess
import sys
import unittest

import alarm


ROOT = Path(__file__).resolve().parents[1]


class FakeClock:
    def __init__(self):
        self.wall = datetime(2026, 11, 20, 23, 59, 58)
        self.elapsed = 100.0
        self.sleeps = []

    def now(self):
        return self.wall

    def monotonic(self):
        return self.elapsed

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.elapsed += seconds
        self.wall += timedelta(seconds=seconds)


class ParsingTests(unittest.TestCase):
    def test_duration_units_and_limits(self):
        for value, expected in [("1s", 1), ("10m", 600), ("24h", 86400), ("86400s", 86400)]:
            with self.subTest(value=value):
                self.assertEqual(alarm.parse_duration(value), expected)

    def test_invalid_durations(self):
        for value in ["0s", "-1m", "1.5h", "25h", "86401s", "10", "1h30m", "NaN", "9" * 5000 + "s"]:
            with self.subTest(value=value[:30]):
                with self.assertRaises(argparse.ArgumentTypeError):
                    alarm.parse_duration(value)

    def test_clock_time(self):
        self.assertEqual(alarm.parse_clock_time("00:00"), (0, 0, 0))
        self.assertEqual(alarm.parse_clock_time("23:59:59"), (23, 59, 59))
        for value in ["24:00", "12:60", "12:00:60", "7:30", "12:00pm", "-1:00"]:
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    alarm.parse_clock_time(value)

    def test_label_rejects_terminal_controls_and_empty(self):
        self.assertEqual(alarm.parse_label(" Tea break "), "Tea break")
        for label in [" ", "line\nbreak", "\x1b[31mred", "x" * 121]:
            with self.assertRaises(argparse.ArgumentTypeError):
                alarm.parse_label(label)


class SchedulingTests(unittest.TestCase):
    def test_future_time_today(self):
        now = datetime(2026, 11, 20, 7, 0)
        self.assertEqual(alarm.next_occurrence((7, 30, 0), now), datetime(2026, 11, 20, 7, 30))

    def test_past_equal_and_fractional_time_roll_to_next_day(self):
        for now in [datetime(2026, 12, 31, 7, 30), datetime(2026, 12, 31, 7, 30, 0, 1), datetime(2026, 12, 31, 23, 59)]:
            self.assertEqual(alarm.next_occurrence((7, 30, 0), now), datetime(2027, 1, 1, 7, 30))

    def test_midnight(self):
        self.assertEqual(alarm.next_occurrence((0, 0, 0), FakeClock().now()), datetime(2026, 11, 21))


class RunningTests(unittest.TestCase):
    def run_alarm(self, argv, clock, sleep=None):
        output = io.StringIO()
        with redirect_stdout(output):
            code = alarm.main(argv, now=clock.now, monotonic=clock.monotonic, sleep=sleep or clock.sleep)
        return code, output.getvalue()

    def test_countdown_fires_once_despite_backward_wall_clock_jump(self):
        clock = FakeClock()

        def sleep(seconds):
            clock.sleep(seconds)
            clock.wall -= timedelta(hours=1)

        code, output = self.run_alarm(["--in", "3s", "--label", "Tea"], clock, sleep)
        self.assertEqual(code, 0)
        self.assertEqual(clock.elapsed, 103)
        self.assertEqual(output.count("ALARM: Tea"), 1)
        self.assertIn("\a", output)
        self.assertTrue(all(0 < seconds <= 1 for seconds in clock.sleeps))

    def test_clock_alarm_crosses_midnight_and_silent_has_no_bell(self):
        clock = FakeClock()
        code, output = self.run_alarm(["--at", "00:00", "--silent"], clock)
        self.assertEqual(code, 0)
        self.assertIn("2026-11-21 00:00:00", output)
        self.assertEqual(clock.elapsed, 102)
        self.assertNotIn("\a", output)
        self.assertIn("ALARM: Alarm", output)

    def test_wall_clock_alarm_waits_through_backward_adjustment(self):
        clock = FakeClock()

        def sleep(seconds):
            clock.sleep(seconds)
            if len(clock.sleeps) == 1:
                clock.wall -= timedelta(seconds=2)

        code, _ = self.run_alarm(["--at", "00:00"], clock, sleep)
        self.assertEqual(code, 0)
        self.assertEqual(clock.elapsed, 104)

    def test_wall_clock_jump_past_target_still_fires(self):
        clock = FakeClock()

        def sleep(seconds):
            clock.sleep(seconds)
            clock.wall += timedelta(hours=1)

        code, output = self.run_alarm(["--at", "00:00"], clock, sleep)
        self.assertEqual(code, 0)
        self.assertEqual(len(clock.sleeps), 1)
        self.assertEqual(output.count("ALARM:"), 1)

    def test_early_wakeup_and_oversleep(self):
        for increment in [0.25, 10]:
            clock = FakeClock()

            def sleep(seconds):
                clock.sleep(increment)

            code, output = self.run_alarm(["--in", "2s"], clock, sleep)
            self.assertEqual(code, 0)
            self.assertGreaterEqual(clock.elapsed, 102)
            self.assertEqual(output.count("ALARM:"), 1)

    def test_interrupt_cancels_without_firing(self):
        def interrupt(seconds):
            raise KeyboardInterrupt

        for argv in [["--in", "10m"], ["--at", "00:00"]]:
            code, output = self.run_alarm(argv, FakeClock(), interrupt)
            self.assertEqual(code, 130)
            self.assertIn("Alarm cancelled.", output)
            self.assertNotIn("ALARM:", output)


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "alarm.py"), *args], capture_output=True, text=True, timeout=5)

    def test_help(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--silent", result.stdout)

    def test_invalid_cli_exits_two_without_traceback(self):
        for args in [[], ["--in", "0s"], ["--in", "1s", "--at", "07:30"], ["--at", "25:00"], ["--label", "x"]]:
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_real_short_alarm(self):
        result = self.invoke("--in", "1s", "--silent", "--label", "Demo")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Alarm in 1s", result.stdout)
        self.assertEqual(result.stdout.count("ALARM: Demo"), 1)
        self.assertNotIn("\a", result.stdout)

    @unittest.skipIf(sys.platform == "win32", "POSIX subprocess signal smoke test")
    def test_real_sigint(self):
        with subprocess.Popen([sys.executable, str(ROOT / "alarm.py"), "--in", "1h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            try:
                # Synchronize on flushed startup rather than using a timing guess.
                self.assertIn("Alarm in 3600s", process.stdout.readline())
                process.send_signal(signal.SIGINT)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 130)
                self.assertIn("Alarm cancelled.", stdout)
                self.assertNotIn("ALARM:", stdout)
                self.assertEqual(stderr, "")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()


if __name__ == "__main__":
    unittest.main()
