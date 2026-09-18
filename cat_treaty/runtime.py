"""Deployment-neutral runtime configuration for the CT6 API."""

from __future__ import annotations

from dataclasses import dataclass
import os


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    cors_origins: tuple[str, ...] = ()
    cors_allow_credentials: bool = False

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must be non-empty")
        if not 1 <= self.port <= 65_535:
            raise ValueError("port must be between 1 and 65535")
        if self.log_level not in {"critical", "error", "warning", "info", "debug", "trace"}:
            raise ValueError("unsupported log level")
        if any(not origin.strip() for origin in self.cors_origins):
            raise ValueError("CORS origins must be non-empty")
        if "*" in self.cors_origins:
            raise ValueError("wildcard CORS is not permitted by the CT6 production contract")

    @classmethod
    def from_environment(cls) -> "RuntimeSettings":
        raw_origins = os.getenv("CT6_CORS_ORIGINS", "")
        origins = tuple(item.strip() for item in raw_origins.split(",") if item.strip())
        raw_port = os.getenv("PORT", os.getenv("CT6_PORT", "8000"))
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("PORT must be an integer") from error
        return cls(
            host=os.getenv("CT6_HOST", "0.0.0.0"),
            port=port,
            log_level=os.getenv("CT6_LOG_LEVEL", "info").lower(),
            cors_origins=origins,
            cors_allow_credentials=_boolean("CT6_CORS_ALLOW_CREDENTIALS", False),
        )
