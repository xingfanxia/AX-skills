from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from process_launcher.models import PeriodicJobConfig, PeriodicSchedule
from process_launcher.periodic import next_run_after


def _job(schedule: PeriodicSchedule) -> PeriodicJobConfig:
    return PeriodicJobConfig(label="demo", command=["python", "demo.py"], schedule=schedule)


def test_next_daily_run_same_day() -> None:
    schedule = PeriodicSchedule(type="daily", time="19:00", timezone="America/Los_Angeles")
    after = datetime(2026, 6, 5, 18, 30, tzinfo=ZoneInfo("America/Los_Angeles"))

    assert next_run_after(_job(schedule), after) == datetime(2026, 6, 5, 19, 0, tzinfo=ZoneInfo("America/Los_Angeles"))


def test_next_daily_run_rolls_to_tomorrow() -> None:
    schedule = PeriodicSchedule(type="daily", time="19:00", timezone="America/Los_Angeles")
    after = datetime(2026, 6, 5, 19, 1, tzinfo=ZoneInfo("America/Los_Angeles"))

    assert next_run_after(_job(schedule), after) == datetime(2026, 6, 6, 19, 0, tzinfo=ZoneInfo("America/Los_Angeles"))


def test_next_weekly_run() -> None:
    schedule = PeriodicSchedule(
        type="weekly",
        days_of_week=["thu"],
        time="07:30",
        timezone="America/Los_Angeles",
    )
    after = datetime(2026, 6, 5, 12, 0, tzinfo=ZoneInfo("America/Los_Angeles"))

    assert next_run_after(_job(schedule), after) == datetime(2026, 6, 11, 7, 30, tzinfo=ZoneInfo("America/Los_Angeles"))


def test_next_interval_run() -> None:
    schedule = PeriodicSchedule(type="interval", every_seconds=120)
    after = datetime(2026, 6, 5, 12, 0, tzinfo=ZoneInfo("UTC"))

    assert next_run_after(_job(schedule), after) == datetime(2026, 6, 5, 12, 2, tzinfo=ZoneInfo("UTC"))


def test_next_cron_run_supports_common_fields() -> None:
    schedule = PeriodicSchedule(type="cron", expression="0 6,9,12,21 * * *", timezone="America/Los_Angeles")
    after = datetime(2026, 6, 5, 6, 1, tzinfo=ZoneInfo("America/Los_Angeles"))

    assert next_run_after(_job(schedule), after) == datetime(2026, 6, 5, 9, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
