# pyright: reportMissingImports=false
"""回归测试：recover_pending 比较 tz-aware 的 run_at 不应崩。

历史 bug：job.run_at 可能带时区（aware），datetime.now() 是 naive，
`job.run_at > datetime.now()` 抛 "can't compare offset-naive and offset-aware
datetimes"，导致 launcher 启动时 recover_pending 失败、整个服务起不来。
"""
from __future__ import annotations

import pytest

from datetime import datetime, timedelta, timezone
from pathlib import Path

from process_launcher.log import HeartbeatLogger, OutputLogger
from process_launcher.models import (
    MisfirePolicy,
    ScheduledJob,
    ScheduledStatus,
)
from process_launcher.process import ProcessManager
from process_launcher.scheduled import ScheduledManager
from process_launcher.storage import SQLiteStore


def _make_manager(tmp_path: Path) -> tuple[ScheduledManager, ProcessManager]:
    store = SQLiteStore(tmp_path / "launcher.db")
    sched = ScheduledManager(store)
    pm = ProcessManager(HeartbeatLogger(tmp_path / "logs"), OutputLogger(tmp_path / "logs"))
    return sched, pm


def _job(run_at: datetime, misfire: MisfirePolicy) -> ScheduledJob:
    return ScheduledJob(
        label="tz_job",
        command=["true"],
        scheduled_at=datetime.now(),
        run_at=run_at,
        status=ScheduledStatus.PENDING,
        misfire_policy=misfire,
    )


def test_recover_pending_handles_tz_aware_past_run_at(tmp_path):
    """带时区、已过期的 run_at（SKIP 策略）：不崩，标记为 missed。"""
    sched, pm = _make_manager(tmp_path)
    past_aware = datetime.now(timezone(timedelta(hours=-7))) - timedelta(hours=1)
    sched.store.upsert_scheduled_job(_job(past_aware, MisfirePolicy.SKIP))

    sched.recover_pending(pm)  # 不应抛异常

    jobs = sched.store.list_scheduled_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == ScheduledStatus.MISSED


@pytest.mark.asyncio
async def test_recover_pending_handles_tz_aware_future_run_at(tmp_path):
    """带时区、未来的 run_at：不崩，重新排程（仍 pending）。"""
    sched, pm = _make_manager(tmp_path)
    future_aware = datetime.now(timezone(timedelta(hours=-7))) + timedelta(days=1)
    sched.store.upsert_scheduled_job(_job(future_aware, MisfirePolicy.SKIP))

    sched.recover_pending(pm)  # 不应抛异常

    jobs = sched.store.list_scheduled_jobs()
    assert jobs[0].status == ScheduledStatus.PENDING


def test_recover_pending_naive_still_works(tmp_path):
    """naive run_at（原本就支持的）仍正常。"""
    sched, pm = _make_manager(tmp_path)
    past_naive = datetime.now() - timedelta(hours=1)
    sched.store.upsert_scheduled_job(_job(past_naive, MisfirePolicy.SKIP))

    sched.recover_pending(pm)

    assert sched.store.list_scheduled_jobs()[0].status == ScheduledStatus.MISSED


@pytest.mark.asyncio
async def test_recover_pending_mixed_tz_and_naive(tmp_path):
    """同时存在 aware 和 naive 的 pending job（正是触发线上崩溃的场景）：不崩。"""
    sched, pm = _make_manager(tmp_path)
    aware = datetime.now(timezone(timedelta(hours=-7))) + timedelta(days=1)
    naive = datetime.now() + timedelta(days=2)
    sched.store.upsert_scheduled_job(_job(aware, MisfirePolicy.SKIP))
    sched.store.upsert_scheduled_job(_job(naive, MisfirePolicy.SKIP))

    sched.recover_pending(pm)  # 不应抛异常

    assert len(sched.store.list_scheduled_jobs()) == 2
