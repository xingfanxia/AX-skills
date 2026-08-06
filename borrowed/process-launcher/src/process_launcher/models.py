from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProcessStatus(str, Enum):
    RUNNING = "running"
    EXITED = "exited"
    KILLED = "killed"
    CIRCUIT_BREAKER = "circuit_breaker"


class ProcessInfo(BaseModel):
    pid: int
    label: str | None = None
    command: str
    cwd: str | None = None
    status: ProcessStatus
    exit_code: int | None = None
    started_at: datetime
    exited_at: datetime | None = None
    output_file: str | None = None
    restart_count: int = 0


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: list[str] | str
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    label: str | None = None
    timeout: float | None = Field(default=None, gt=0)
    delay_seconds: float | None = Field(default=None, ge=0, description="Delay execution by N seconds. Persisted across restarts.")
    run_at: datetime | None = Field(default=None, description="Absolute time to run the command.")
    misfire_policy: "MisfirePolicy" = Field(default="run_immediately")

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        if self.delay_seconds is not None and self.delay_seconds > 0 and self.run_at is not None:
            raise ValueError("delay_seconds and run_at cannot both be set")
        return self


class RunResponse(BaseModel):
    pid: int
    label: str | None = None
    started_at: datetime
    output_file: str | None = None


class ScheduledUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_at: datetime | None = Field(default=None, description="New absolute launch time.")
    label: str | None = None
    timeout: float | None = Field(default=None, gt=0)
    misfire_policy: "MisfirePolicy | None" = None

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        if self.run_at is None and self.label is None and self.timeout is None and self.misfire_policy is None:
            raise ValueError("at least one scheduled job field must be provided")
        return self


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7997


class LoggingConfig(BaseModel):
    dir: str = "logs"
    heartbeat_retention_days: int = 30
    output_retention_days: int = 30


class StorageConfig(BaseModel):
    sqlite_path: str = "state/launcher.db"


class ServiceConfig(BaseModel):
    label: str
    command: list[str] | str
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    env_file: str | None = None
    restart_delay: float = 10.0
    max_restarts: int = 3
    restart_window: float = 60.0

    @field_validator("command")
    @classmethod
    def validate_command(cls, value: list[str] | str) -> list[str] | str:
        if isinstance(value, list) and not value:
            raise ValueError("command must not be empty")
        if isinstance(value, str) and not value.strip():
            raise ValueError("command must not be empty")
        return value

    def resolved_env_file(self) -> Path | None:
        if not self.env_file:
            return None
        env_path = Path(self.env_file)
        if env_path.is_absolute() or not self.cwd:
            return env_path
        return Path(self.cwd) / env_path


class PeriodicSchedule(BaseModel):
    type: str
    time: str | None = None
    timezone: str = "UTC"
    days_of_week: list[str] = Field(default_factory=list)
    every_seconds: float | None = Field(default=None, gt=0)
    expression: str | None = None

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        if self.type == "daily":
            if not self.time:
                raise ValueError("daily schedule requires time")
        elif self.type == "weekly":
            if not self.time:
                raise ValueError("weekly schedule requires time")
            if not self.days_of_week:
                raise ValueError("weekly schedule requires days_of_week")
        elif self.type == "interval":
            if self.every_seconds is None:
                raise ValueError("interval schedule requires every_seconds")
        elif self.type == "cron":
            if not self.expression:
                raise ValueError("cron schedule requires expression")
        else:
            raise ValueError("schedule type must be daily, weekly, interval, or cron")
        return self


class PeriodicOverlapPolicy(str, Enum):
    SKIP = "skip"
    RUN_CONCURRENTLY = "run_concurrently"


class MisfirePolicy(str, Enum):
    RUN_IMMEDIATELY = "run_immediately"
    SKIP = "skip"
    FAIL = "fail"


class PeriodicJobConfig(BaseModel):
    label: str
    command: list[str] | str
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    env_file: str | None = None
    timeout: float | None = Field(default=None, gt=0)
    enabled: bool = True
    schedule: PeriodicSchedule
    overlap_policy: PeriodicOverlapPolicy = PeriodicOverlapPolicy.SKIP
    misfire_policy: MisfirePolicy = MisfirePolicy.SKIP

    @field_validator("command")
    @classmethod
    def validate_command(cls, value: list[str] | str) -> list[str] | str:
        if isinstance(value, list) and not value:
            raise ValueError("command must not be empty")
        if isinstance(value, str) and not value.strip():
            raise ValueError("command must not be empty")
        return value

    def resolved_env_file(self) -> Path | None:
        if not self.env_file:
            return None
        env_path = Path(self.env_file)
        if env_path.is_absolute() or not self.cwd:
            return env_path
        return Path(self.cwd) / env_path


class LauncherConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    periodic_jobs: dict[str, PeriodicJobConfig] = Field(default_factory=dict)


class ScheduledStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MISSED = "missed"


class PeriodicRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PeriodicRun(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    label: str
    command: list[str] | str
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float | None = None
    scheduled_for: datetime
    status: PeriodicRunStatus = PeriodicRunStatus.PENDING
    trigger: str = "schedule"
    result_pid: int | None = None
    output_file: str | None = None
    last_error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class PeriodicRuntime(BaseModel):
    next_run_at: datetime | None = None
    last_run_status: PeriodicRunStatus | None = None
    last_run_at: datetime | None = None
    active_pid: int | None = None


class PeriodicJobState(BaseModel):
    label: str
    declared: PeriodicJobConfig
    runtime: PeriodicRuntime


class PeriodicReloadResult(BaseModel):
    status: str
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)


class ScheduledJob(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    label: str | None = None
    command: list[str] | str
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float | None = None
    scheduled_at: datetime
    run_at: datetime
    status: ScheduledStatus = ScheduledStatus.PENDING
    misfire_policy: MisfirePolicy = MisfirePolicy.RUN_IMMEDIATELY
    result_pid: int | None = None
    last_error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
