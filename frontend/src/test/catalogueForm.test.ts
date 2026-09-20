import { buildCatalogueRequest, errorsFromProblem, initialCatalogueForm } from "../features/explore/catalogueForm";

describe("strict catalogue request builder", () => {
  it("serializes a complete CT6 catalogue request without calculated results", () => {
    const built = buildCatalogueRequest(initialCatalogueForm);
    expect(built.errors).toEqual({});
    expect(built.request).toMatchObject({
      api_schema_version: "ct6.0",
      response_detail: "full",
      input: {
        simulation: { trial_count: 1, catalogue_source_mode: "supplied", simulation_seed: null },
        trials: [{ occurrences: [{ loss_basis: { initial_insured_loss: 45_000_000 } }] }],
        program: { program_id: "P1", layers: [{ layer_id: "L1" }] },
        treaty_terms: { program_id: "P1", layer_terms: [{ layer_id: "L1" }] },
      },
    });
    expect(JSON.stringify(built.request)).not.toMatch(/LossBasisResult|InuringWaterfallResult|reconciliation_passed|pre_capacity|post_capacity|analytics|result_hash/i);
  });

  it("enforces catalogue seed semantics and finite bounded inputs", () => {
    const generated = buildCatalogueRequest({ ...initialCatalogueForm, sourceMode: "generated", simulationSeed: "42" });
    expect(generated.request?.input.simulation.simulation_seed).toBe(42);

    const invalid = buildCatalogueRequest({ ...initialCatalogueForm, sourceMode: "supplied", simulationSeed: "42", cededShare: "1.2", insuredLoss: "NaN" });
    expect(invalid.request).toBeNull();
    expect(invalid.errors).toMatchObject({
      simulationSeed: expect.any(String),
      cededShare: expect.any(String),
      insuredLoss: expect.any(String),
    });
  });

  it("maps CT6 path evidence back to the controlled input", () => {
    const errors = errorsFromProblem({
      type: "about:blank",
      title: "Invalid request",
      status: 422,
      detail: "The request is invalid.",
      instance: "/api/v1/runs/catalogue",
      request_id: "request-1",
      code: "CT6_SCHEMA_VALIDATION",
      errors: [{
        path: "input.program.layers.0.attachment",
        code: "CT6_SCHEMA_VALIDATION",
        message: "Attachment is invalid.",
        rule_reference: "CT3",
      }],
    });
    expect(errors).toEqual({ attachment: "Attachment is invalid." });
  });
});
