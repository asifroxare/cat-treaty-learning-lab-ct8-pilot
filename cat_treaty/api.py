"""CT6 FastAPI transport contract; actuarial work remains in CT2--CT5."""

from __future__ import annotations

import json
import re
import types
from collections.abc import Callable
from enum import Enum
from typing import Any
from typing import Annotated, get_args, get_origin
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from cat_treaty.ct2_metadata import CT2_ENGINE_VERSION, CT2_SCHEMA_VERSION
from cat_treaty.ct3_metadata import CT3_ENGINE_VERSION, CT3_SCHEMA_VERSION
from cat_treaty.ct4_metadata import CT4_ENGINE_VERSION, CT4_SCHEMA_VERSION
from cat_treaty.ct4_models import HoursElectionMethod
from cat_treaty.ct5_metadata import CT5_ENGINE_VERSION, CT5_SCHEMA_VERSION
from cat_treaty.ct6_hours import CT6HoursContractBlockedError, run_hours_clause
from cat_treaty.ct6_models import (
    CT6_API_VERSION, CT6_SCHEMA_VERSION, CT6ErrorItem, CT6ProblemResponse,
    CT6SuccessResponse, CatalogueRunRequest, CatalogueSourceMode,
    HoursRunRequest, ResponseDetail, RunMode,
)
from cat_treaty.ct6_orchestration import run_catalogue
from cat_treaty.ct6_responses import project_catalogue_success, project_hours_success
from cat_treaty.models import CapacityBasis, SettlementMode
from cat_treaty.simulation import CT4PreflightError
from cat_treaty.runtime import RuntimeSettings

MAX_REQUEST_BYTES = 25 * 1024 * 1024
MAX_CATALOGUE_TRIALS = 10_000
MAX_CATALOGUE_OCCURRENCES = 100_000
MAX_LAYERS = 4
MAX_HOURS_COMPONENTS = 12
MAX_FULL_DETAIL_ROWS = 25_000
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

_MESSAGES = {
    "CT6_MALFORMED_JSON": ("Malformed request body", "The request body must be valid JSON with the application/json media type."),
    "CT6_VERSION_CONFLICT": ("API schema version conflict", "The requested API schema version is not supported."),
    "CT6_REQUEST_TOO_LARGE": ("Request exceeds a frozen limit", "The request exceeds a CT6 synchronous or full-detail response limit."),
    "CT6_SCHEMA_VALIDATION": ("Schema validation failed", "The request does not match the strict CT6 wire schema."),
    "CT6_DOMAIN_VALIDATION": ("Domain validation failed", "The request violates the treaty contract."),
    "CT6_CONTRACT_BLOCKED": ("Contract evaluation blocked", "The validated contract cannot produce an authoritative recovery result."),
    "CT6_INTERNAL_ERROR": ("Internal server error", "The request could not be completed because of an unexpected server failure."),
    "CT6_NOT_READY": ("Service not ready", "One or more required engine contracts are unavailable."),
}


def create_app(*, settings: RuntimeSettings | None = None) -> FastAPI:
    runtime = settings or RuntimeSettings.from_environment()
    application = FastAPI(
        title="EdInsured Catastrophe Treaty Learning Lab API",
        version=CT6_API_VERSION,
        description="Strict CT6 transport over the frozen CT2--CT5 engines.",
    )
    if runtime.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(runtime.cors_origins),
            allow_credentials=runtime.cors_allow_credentials,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-Request-ID"],
        )

    @application.middleware("http")
    async def request_contract(request: Request, call_next: Callable):
        supplied_id = request.headers.get("X-Request-ID", "")
        request.state.request_id = supplied_id if REQUEST_ID_PATTERN.fullmatch(supplied_id) else str(uuid4())
        if request.method == "POST" and request.url.path.startswith("/api/v1/runs/"):
            content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                return _problem(request, 400, "CT6_MALFORMED_JSON")
            length = request.headers.get("content-length")
            if length is not None:
                try:
                    if int(length) > MAX_REQUEST_BYTES:
                        return _problem(request, 413, "CT6_REQUEST_TOO_LARGE")
                except ValueError:
                    return _problem(request, 400, "CT6_MALFORMED_JSON")
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, error: RequestValidationError):
        validation_errors = error.errors()
        if any(item.get("type") == "json_invalid" for item in validation_errors):
            return _problem(request, 400, "CT6_MALFORMED_JSON")
        try:
            payload = json.loads((await request.body()).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _problem(request, 400, "CT6_MALFORMED_JSON")
        if isinstance(payload, dict):
            version = payload.get("api_schema_version")
            if isinstance(version, str) and version != CT6_SCHEMA_VERSION:
                return _problem(request, 409, "CT6_VERSION_CONFLICT")
        items = tuple(sorted((_schema_error(item) for item in validation_errors), key=lambda item: (item.path, item.code)))
        return _problem(request, 422, "CT6_SCHEMA_VALIDATION", errors=items)

    @application.get("/", tags=["service"])
    async def root() -> dict[str, str]:
        return {"product": "cat-treaty-learning-lab", "api_version": CT6_API_VERSION, "status": "available"}

    @application.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "live", "api_version": CT6_API_VERSION}

    @application.get("/health/ready", tags=["health"], responses={503: {"model": CT6ProblemResponse}})
    async def ready(request: Request):
        checks = _readiness_checks()
        if not all(checks.values()):
            return _problem(request, 503, "CT6_NOT_READY")
        return {"status": "ready", "checks": checks}

    @application.get("/api/v1/capabilities", tags=["contract"])
    async def capabilities() -> dict[str, object]:
        return _capabilities()

    # Python 3.14 changed two stdlib reason phrases. Freeze the CT6 OpenAPI
    # descriptions so every supported Python version emits one contract.
    error_descriptions = {
        400: "Bad Request",
        409: "Conflict",
        413: "Request Entity Too Large",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }
    common_errors = {
        code: {"model": CT6ProblemResponse, "description": description}
        for code, description in error_descriptions.items()
    }

    @application.post("/api/v1/runs/catalogue", response_model=CT6SuccessResponse, responses=common_errors, tags=["runs"])
    async def catalogue(request: Request):
        size_problem = await _actual_size_problem(request)
        if size_problem is not None:
            return size_problem
        body = await _validated_body(request, CatalogueRunRequest)
        if isinstance(body, JSONResponse):
            return body
        if body.response_detail is ResponseDetail.FULL and _catalogue_occurrence_count(body) > MAX_FULL_DETAIL_ROWS:
            return _problem(request, 413, "CT6_REQUEST_TOO_LARGE")
        try:
            result = run_catalogue(body)
            return project_catalogue_success(result, request_id=request.state.request_id)
        except CT4PreflightError:
            return _problem(request, 422, "CT6_CONTRACT_BLOCKED", errors=_contract_errors())
        except (TypeError, ValueError):
            return _problem(request, 422, "CT6_DOMAIN_VALIDATION", errors=_domain_errors())
        except Exception:
            return _problem(request, 500, "CT6_INTERNAL_ERROR")

    @application.post("/api/v1/runs/hours-clause", response_model=CT6SuccessResponse, responses=common_errors, tags=["runs"])
    async def hours_clause(request: Request):
        size_problem = await _actual_size_problem(request)
        if size_problem is not None:
            return size_problem
        body = await _validated_body(request, HoursRunRequest)
        if isinstance(body, JSONResponse):
            return body
        try:
            result = run_hours_clause(body)
            return project_hours_success(result, request_id=request.state.request_id)
        except CT6HoursContractBlockedError:
            return _problem(request, 422, "CT6_CONTRACT_BLOCKED", errors=_contract_errors())
        except (TypeError, ValueError):
            return _problem(request, 422, "CT6_DOMAIN_VALIDATION", errors=_domain_errors())
        except Exception:
            return _problem(request, 500, "CT6_INTERNAL_ERROR")

    generated_openapi = application.openapi

    def contract_openapi() -> dict[str, Any]:
        if application.openapi_schema is not None:
            return application.openapi_schema
        schema = generated_openapi()
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        for model in (CatalogueRunRequest, HoursRunRequest):
            model_schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
            components.update(model_schema.pop("$defs", {}))
            components[model.__name__] = model_schema
        for path, model in (
            ("/api/v1/runs/catalogue", CatalogueRunRequest),
            ("/api/v1/runs/hours-clause", HoursRunRequest),
        ):
            schema["paths"][path]["post"]["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{model.__name__}"}}},
            }
        application.openapi_schema = schema
        return schema

    application.openapi = contract_openapi
    return application


async def _actual_size_problem(request: Request) -> JSONResponse | None:
    return _problem(request, 413, "CT6_REQUEST_TOO_LARGE") if len(await request.body()) > MAX_REQUEST_BYTES else None


async def _validated_body(request: Request, model: type[BaseModel]) -> BaseModel | JSONResponse:
    try:
        payload = json.loads((await request.body()).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _problem(request, 400, "CT6_MALFORMED_JSON")
    if isinstance(payload, dict):
        version = payload.get("api_schema_version")
        if isinstance(version, str) and version != CT6_SCHEMA_VERSION:
            return _problem(request, 409, "CT6_VERSION_CONFLICT")
    try:
        return model.model_validate(_normalize_json_value(model, payload))
    except ValidationError as error:
        validation_errors = error.errors()
        items = tuple(sorted((_schema_error(item) for item in validation_errors), key=lambda item: (item.path, item.code)))
        if validation_errors and all(item.get("type") == "value_error" for item in validation_errors):
            domain_items = tuple(
                CT6ErrorItem(
                    path=item.path,
                    code="CT6_DOMAIN_RULE_VIOLATION",
                    message="A frozen treaty-domain rule was not satisfied.",
                    rule_reference="CT6-section-9-12",
                )
                for item in items
            )
            return _problem(request, 422, "CT6_DOMAIN_VALIDATION", errors=domain_items)
        return _problem(request, 422, "CT6_SCHEMA_VALIDATION", errors=items)


def _normalize_json_value(annotation: Any, value: Any) -> Any:
    """Convert only JSON representation types required by strict wire models."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Annotated:
        return _normalize_json_value(args[0], value)
    if origin in (types.UnionType, getattr(__import__("typing"), "Union")):
        for option in args:
            if option is type(None) and value is None:
                return None
            normalized = _normalize_json_value(option, value)
            if normalized is not value:
                return normalized
        return value
    if origin is tuple and isinstance(value, list):
        item_type = args[0] if args else Any
        return tuple(_normalize_json_value(item_type, item) for item in value)
    if isinstance(annotation, type) and issubclass(annotation, Enum) and isinstance(value, str):
        try:
            return annotation(value)
        except ValueError:
            return value
    if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
        return {
            key: _normalize_json_value(annotation.model_fields[key].annotation, item) if key in annotation.model_fields else item
            for key, item in value.items()
        }
    return value


def _problem(request: Request, status: int, code: str, *, errors: tuple[CT6ErrorItem, ...] = ()) -> JSONResponse:
    title, detail = _MESSAGES[code]
    slug = code.removeprefix("CT6_").lower().replace("_", "-")
    model = CT6ProblemResponse(
        type=f"https://edinsured.example/problems/{slug}", title=title, status=status,
        code=code, detail=detail, instance=request.url.path,
        request_id=request.state.request_id, errors=errors,
    )
    return JSONResponse(status_code=status, content=model.model_dump(mode="json"), headers={"X-Request-ID": request.state.request_id})


def _schema_error(error: dict[str, Any]) -> CT6ErrorItem:
    location = tuple(part for part in error.get("loc", ()) if part != "body")
    path = ""
    for part in location:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += ("." if path else "") + str(part)
    path = path or "request"
    return CT6ErrorItem(path=path, code="CT6_FIELD_INVALID", message="A request field failed strict schema validation.", rule_reference="CT6-section-8-9")


def _contract_errors() -> tuple[CT6ErrorItem, ...]:
    return (CT6ErrorItem(path="input", code="CT6_CONTRACT_INELIGIBLE", message="Contractual eligibility checks blocked calculation.", rule_reference="CT6-section-10-12"),)


def _domain_errors() -> tuple[CT6ErrorItem, ...]:
    return (CT6ErrorItem(path="input", code="CT6_DOMAIN_RULE_VIOLATION", message="A frozen treaty-domain rule was not satisfied.", rule_reference="CT6-section-9-12"),)


def _catalogue_occurrence_count(request: CatalogueRunRequest) -> int:
    return sum(len(trial.occurrences) for trial in request.input.trials)


def _readiness_checks() -> dict[str, bool]:
    return {
        "ct2_contract": bool(CT2_ENGINE_VERSION and CT2_SCHEMA_VERSION),
        "ct3_contract": bool(CT3_ENGINE_VERSION and CT3_SCHEMA_VERSION),
        "ct4_contract": bool(CT4_ENGINE_VERSION and CT4_SCHEMA_VERSION),
        "ct5_contract": bool(CT5_ENGINE_VERSION and CT5_SCHEMA_VERSION),
        "ct6_contract": bool(CT6_API_VERSION and CT6_SCHEMA_VERSION),
    }


def _capabilities() -> dict[str, object]:
    return {
        "product": "cat-treaty-learning-lab",
        "versions": {"ct2_engine": CT2_ENGINE_VERSION, "ct2_schema": CT2_SCHEMA_VERSION, "ct3_engine": CT3_ENGINE_VERSION, "ct3_schema": CT3_SCHEMA_VERSION, "ct4_engine": CT4_ENGINE_VERSION, "ct4_schema": CT4_SCHEMA_VERSION, "ct5_engine": CT5_ENGINE_VERSION, "ct5_schema": CT5_SCHEMA_VERSION, "ct6_api": CT6_API_VERSION, "ct6_schema": CT6_SCHEMA_VERSION},
        "run_modes": [item.value for item in RunMode],
        "catalogue_source_modes": [item.value for item in CatalogueSourceMode],
        "response_detail_modes": [item.value for item in ResponseDetail],
        "settlement_modes": [item.value for item in SettlementMode],
        "capacity_bases": [item.value for item in CapacityBasis],
        "hours_election_methods": [item.value for item in HoursElectionMethod],
        "tolerance_profile": {"relative_tolerance": 1e-12, "absolute_currency_tolerance": 1e-6},
        "limits": {"request_body_bytes": MAX_REQUEST_BYTES, "catalogue_trials": MAX_CATALOGUE_TRIALS, "catalogue_occurrences": MAX_CATALOGUE_OCCURRENCES, "layers": MAX_LAYERS, "hours_clause_components": MAX_HOURS_COMPONENTS, "full_detail_occurrence_rows": MAX_FULL_DETAIL_ROWS},
    }


app = create_app()
