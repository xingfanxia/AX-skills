from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXIT_USAGE = 2
EXIT_UNSUPPORTED = 3
EXIT_AUTH = 4
EXIT_STALE = 5
EXIT_DEPENDENCY = 6
EXIT_IO = 7
EXIT_PARTIAL = 8
EXIT_BACKEND = 9
EXIT_LOCKED = 10


@dataclass(slots=True)
class ApplePhotosError(Exception):
    code: str
    message: str
    exit_code: int
    detail: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "exception_type": type(self).__name__,
        }
        if self.detail:
            value["detail"] = self.detail
        return value


def usage_error(message: str, *, code: str = "E_USAGE") -> ApplePhotosError:
    return ApplePhotosError(code, message, EXIT_USAGE)


def unsupported(message: str, *, code: str = "E_CAPABILITY_UNSUPPORTED") -> ApplePhotosError:
    return ApplePhotosError(code, message, EXIT_UNSUPPORTED)


def stale(
    message: str, *, code: str = "E_PLAN_STALE", detail: dict[str, Any] | None = None
) -> ApplePhotosError:
    return ApplePhotosError(code, message, EXIT_STALE, detail)
