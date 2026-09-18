"""CT6 OpenAPI contract and generated-model tests."""

from cat_treaty.api import create_app


def test_every_run_route_references_success_and_problem_models() -> None:
    schema = create_app().openapi()
    for path, request_model in (
        ("/api/v1/runs/catalogue", "CatalogueRunRequest"),
        ("/api/v1/runs/hours-clause", "HoursRunRequest"),
    ):
        operation = schema["paths"][path]["post"]
        assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(request_model)
        assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("CT6SuccessResponse")
        for status in ("400", "409", "413", "422", "500"):
            assert operation["responses"][status]["content"]["application/json"]["schema"]["$ref"].endswith("CT6ProblemResponse")


def test_authoritative_three_way_and_utilization_fields_are_in_schema() -> None:
    components = create_app().openapi()["components"]["schemas"]
    occurrence = components["PostCapacityOccurrenceResponse"]["properties"]
    assert {"gross_contractual_recovery", "reinstatement_premium_payable", "net_cash_settlement"} <= set(occurrence)
    utilization = components["PostCapacityLayerAnnualResponse"]["properties"]
    assert {"realized_capacity_utilization", "realized_capacity_utilization_status"} <= set(utilization)

