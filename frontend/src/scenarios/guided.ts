import type { CatalogueRunRequest, HoursRunRequest } from "../api/contract";
import { buildCatalogueRequest, initialCatalogueForm } from "../features/explore/catalogueForm";
import { buildHoursRequest, initialHoursForm } from "../features/hours/hoursForm";

export type GuidedRequest =
  | { readonly mode: "catalogue"; readonly request: CatalogueRunRequest }
  | { readonly mode: "hours_clause"; readonly request: HoursRunRequest };

export interface GuidedExperiment {
  readonly id: `E0${number}`;
  readonly version: "1.0";
  readonly title: string;
  readonly learnerLevel: "foundation" | "intermediate";
  readonly objective: string;
  readonly controlledFields: readonly string[];
  readonly predictionPrompt: string;
  readonly baseline: GuidedRequest;
  readonly scenario: GuidedRequest;
  readonly takeaway: {
    readonly statement: string;
    readonly evidencePaths: readonly string[];
  };
  readonly inspectNext: string;
}

function baseCatalogue(): CatalogueRunRequest {
  const request = buildCatalogueRequest(initialCatalogueForm).request;
  if (!request) throw new Error("Frozen guided catalogue fixture is invalid");
  return structuredClone(request);
}

function baseHours(): HoursRunRequest {
  const request = buildHoursRequest(initialHoursForm).request;
  if (!request) throw new Error("Frozen guided hours fixture is invalid");
  return structuredClone(request);
}

function catalogueScenario(change: (request: CatalogueRunRequest) => void): CatalogueRunRequest {
  const request = baseCatalogue();
  change(request);
  return request;
}

const commonCatalogueEvidence = ["learning.facts", "learning.reconciliations", "identity.ct5_result_hash"] as const;

export const guidedExperiments: readonly GuidedExperiment[] = [
  {
    id: "E01", version: "1.0", title: "From insured loss to subject loss", learnerLevel: "foundation",
    objective: "Observe how one disclosed inuring cover changes the loss reaching the Cat XL program.",
    controlledFields: ["input.trials[0].occurrences[0].inuring_covers[0].cession_rate"],
    predictionPrompt: "Before running, describe how a larger inuring cession may affect the Cat XL subject loss.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => { request.input.trials[0]!.occurrences[0]!.inuring_covers[0]!.cession_rate = 0.2; }) },
    takeaway: { statement: "Inspect the returned CT2 facts and reconciliations to see how the declared inuring cover entered the subject-loss bridge.", evidencePaths: commonCatalogueEvidence },
    inspectNext: "Loss-stage facts and F03–F09 reconciliation evidence.",
  },
  {
    id: "E02", version: "1.0", title: "Move attachment and limit", learnerLevel: "foundation",
    objective: "Hold the occurrence fixed while moving one layer attachment.",
    controlledFields: ["input.program.layers[0].attachment"],
    predictionPrompt: "Before running, describe which returned recovery and retained-loss fields you expect to respond.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => { request.input.program.layers[0]!.attachment = 15_000_000; }) },
    takeaway: { statement: "Use the returned recovery fields and reconciliation evidence to trace the changed layer geometry without treating either structure as preferred.", evidencePaths: commonCatalogueEvidence },
    inspectNext: "Pre-capacity recovery and CT3 reconciliation references.",
  },
  {
    id: "E03", version: "1.0", title: "Shares are different controls", learnerLevel: "foundation",
    objective: "Change placement share while ceded share remains fixed.",
    controlledFields: ["input.program.layers[0].placement_share"],
    predictionPrompt: "Before running, state why ceded share and placement share must not be combined into one input.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => { request.input.program.layers[0]!.placement_share = 0.75; }) },
    takeaway: { statement: "Read the returned recovery and capacity facts with the fixed-share-per-trial caveat; the two contractual shares remain separate inputs.", evidencePaths: commonCatalogueEvidence },
    inspectNext: "Recovery, layer capacity and share declarations.",
  },
  {
    id: "E04", version: "1.0", title: "Annual capacity across events", learnerLevel: "intermediate",
    objective: "Add a later event to the same annual trial and inspect pre/post-capacity treatment.",
    controlledFields: ["input.trials[0].occurrences[1]"],
    predictionPrompt: "Before running, describe where a later event may encounter reduced active capacity.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => {
      const later = structuredClone(request.input.trials[0]!.occurrences[0]!);
      later.event_id = "E2"; later.event_sequence = 2; later.event_time = 200; later.trace_reference = "CT7-E2"; later.loss_basis.occurrence_id = "E2"; later.loss_basis.initial_insured_loss = 35_000_000;
      request.input.trials[0]!.occurrences.push(later);
    }) },
    takeaway: { statement: "Compare the returned pre-capacity entitlement with the post-capacity ledger for each event and retain every reported shortfall.", evidencePaths: ["pre_capacity.occurrence_rows", "post_capacity.occurrence_rows", "learning.reconciliations"] },
    inspectNext: "Ordered occurrence rows, active capacity and shortfall.",
  },
  {
    id: "E05", version: "1.0", title: "Reinstatement economics", learnerLevel: "intermediate",
    objective: "Switch the declared reinstatement tranche from paid to free.",
    controlledFields: ["input.treaty_terms.layer_terms[0].reinstatement_tranches[0].charge_type"],
    predictionPrompt: "Before running, distinguish capacity restored from premium payable and net cash settlement.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => { const tranche = request.input.treaty_terms.layer_terms[0]!.reinstatement_tranches[0]!; tranche.charge_type = "free"; tranche.premium_rate = 0; }) },
    takeaway: { statement: "Keep gross contractual recovery, reinstatement premium payable and net cash settlement as three separate returned fields.", evidencePaths: ["post_capacity.annual_rows", "learning.reconciliations", "identity.ct5_result_hash"] },
    inspectNext: "Three-way settlement and reinstatement ledger.",
  },
  {
    id: "E06", version: "1.0", title: "Tail credibility", learnerLevel: "intermediate",
    objective: "Increase the declared annual-trial sample while keeping treaty terms fixed.",
    controlledFields: ["input.simulation.trial_count", "input.trials"],
    predictionPrompt: "Before running, identify why sample size matters when reading empirical return periods.",
    baseline: { mode: "catalogue", request: baseCatalogue() },
    scenario: { mode: "catalogue", request: catalogueScenario((request) => { request.input.simulation.trial_count = 3; request.input.trials.push({ annual_trial_id: 2, catalogue_source_id: "CAT-2", occurrences: [] }, { annual_trial_id: 3, catalogue_source_id: "CAT-3", occurrences: [] }); }) },
    takeaway: { statement: "Treat every returned credibility warning as cumulative evidence and read it with the declared trial count.", evidencePaths: ["warnings", "request.trial_count", "identity.ct4_result_hash"] },
    inspectNext: "Warnings, sample size and CT4 identity.",
  },
  {
    id: "E07", version: "1.0", title: "Contractual occurrence election", learnerLevel: "intermediate",
    objective: "Apply two authorized election methods to the same timestamped components.",
    controlledFields: ["input.terms.selected_election_method"],
    predictionPrompt: "Before running, explain why an excluded split cannot enter the election even if it appears attractive.",
    baseline: { mode: "hours_clause", request: baseHours() },
    scenario: { mode: "hours_clause", request: (() => { const request = baseHours(); request.input.terms.selected_election_method = "maximum_contractual_recovery"; return request; })() },
    takeaway: { statement: "Inspect the valid-set list, elected set and rejection reasons; contractual admissibility gates election.", evidencePaths: ["pre_capacity.candidate_sets", "pre_capacity.selected_candidate_set_id", "pre_capacity.valid_candidate_set_ids"] },
    inspectNext: "Candidate sets, exclusion evidence and selected election method.",
  },
] as const;
