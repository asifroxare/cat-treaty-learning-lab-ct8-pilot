"""Early structural limits for a separately versioned, opt-in CT8 pilot."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


class PilotLimitExceeded(ValueError):
    """An otherwise valid CT6 workload exceeds the measured pilot envelope."""


@dataclass(frozen=True)
class PilotLimits:
    max_body_bytes: int
    max_trials: int
    max_occurrences: int
    max_layers: int
    max_hours_components: int
    max_requests_per_minute: int
    allow_full_detail: bool

    @classmethod
    def from_json(cls, raw: str) -> "PilotLimits":
        try:
            settings = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("complete explicit pilot limits required") from error
        if not isinstance(settings, dict) or set(settings) != set(cls.__dataclass_fields__):
            raise ValueError("complete explicit pilot limits required")
        limits = cls(**settings)
        bounds = ((limits.max_body_bytes, 1, 1024 * 1024),
                  (limits.max_trials, 1, 1000), (limits.max_occurrences, 1, 2000),
                  (limits.max_layers, 1, 4), (limits.max_hours_components, 1, 12),
                  (limits.max_requests_per_minute, 1, 10))
        if any(type(value) is not int or not low <= value <= high for value, low, high in bounds):
            raise ValueError("invalid pilot limit")
        if type(limits.allow_full_detail) is not bool:
            raise ValueError("invalid pilot detail mode")
        return limits

    def check(self, mode: str, data: Any) -> None:
        """Reject large work before CT6 model validation or taking a child slot."""
        if not isinstance(data, dict) or not isinstance(data.get("input"), dict):
            raise ValueError("invalid pilot request")
        if data.get("response_detail", "full") == "full" and not self.allow_full_detail:
            raise PilotLimitExceeded("full detail unavailable in the pilot")
        body = data["input"]
        program = body.get("program")
        layers = program.get("layers") if isinstance(program, dict) else None
        if not isinstance(layers, list):
            raise ValueError("invalid pilot program")
        if len(layers) > self.max_layers:
            raise PilotLimitExceeded("pilot layer limit exceeded")
        if mode == "catalogue":
            trials = body.get("trials")
            if not isinstance(trials, list):
                raise ValueError("invalid pilot trials")
            if len(trials) > self.max_trials:
                raise PilotLimitExceeded("pilot trial limit exceeded")
            count = 0
            for trial in trials:
                occurrences = trial.get("occurrences") if isinstance(trial, dict) else None
                if not isinstance(occurrences, list):
                    raise ValueError("invalid pilot occurrences")
                count += len(occurrences)
                if count > self.max_occurrences:
                    raise PilotLimitExceeded("pilot occurrence limit exceeded")
            header = body.get("simulation")
            if isinstance(header, dict) and type(header.get("trial_count")) is int and header["trial_count"] > self.max_trials:
                raise PilotLimitExceeded("pilot declared trial limit exceeded")
        elif mode == "hours-clause":
            components = body.get("components")
            if not isinstance(components, list):
                raise ValueError("invalid pilot hours components")
            if len(components) > self.max_hours_components:
                raise PilotLimitExceeded("pilot hours component limit exceeded")
        else:
            raise ValueError("unsupported pilot route")
