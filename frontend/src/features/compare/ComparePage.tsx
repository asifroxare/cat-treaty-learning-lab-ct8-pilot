import { useMemo, useState } from "react";

import type { AuthoritativeSuccessResponse } from "../../api/authoritative";
import { createCT6Client, type CT6Client, type RunResult } from "../../api/client";
import { formatCurrency } from "../../formatting/authoritative";
import { buildCatalogueRequest, initialCatalogueForm } from "../explore/catalogueForm";
import "./ComparePage.css";

export function areComparable(left: AuthoritativeSuccessResponse, right: AuthoritativeSuccessResponse): boolean {
  return left.request.reporting_currency === right.request.reporting_currency
    && left.api.api_schema_version === right.api.api_schema_version;
}

export function ComparePage({ client: suppliedClient }: { client?: CT6Client }) {
  const client = useMemo(() => suppliedClient ?? createCT6Client(), [suppliedClient]);
  const [baselineAttachment, setBaselineAttachment] = useState("10000000");
  const [scenarioAttachment, setScenarioAttachment] = useState("15000000");
  const [baseline, setBaseline] = useState<RunResult | null>(null);
  const [scenario, setScenario] = useState<RunResult | null>(null);
  const [running, setRunning] = useState<"baseline" | "scenario" | null>(null);

  const execute = async (kind: "baseline" | "scenario", attachment: string) => {
    const built = buildCatalogueRequest({ ...initialCatalogueForm, attachment });
    if (!built.request) {
      const invalid: RunResult = { ok: false, state: "schema_error", problem: null, requestId: null };
      if (kind === "baseline") setBaseline(invalid); else setScenario(invalid);
      return;
    }
    setRunning(kind);
    const result = await client.runCatalogue(built.request);
    if (kind === "baseline") setBaseline(result); else setScenario(result);
    setRunning(null);
  };
  const compatible = baseline?.ok && scenario?.ok ? areComparable(baseline.data, scenario.data) : true;

  return (
    <section className="compare-page" aria-labelledby="compare-title">
      <header><p className="page-eyebrow">Compare</p><h1 id="compare-title">Keep baseline and scenario independent</h1><p className="page-lede">Run each complete request separately. Returned values use identical presentation, with no client-calculated difference, ranking or result badge.</p></header>
      <section className="input-change-panel" aria-labelledby="changed-input-title"><h2 id="changed-input-title">Declared controlled input</h2><p>Only <code>input.program.layers[0].attachment</code> is edited in this comparison workspace.</p></section>
      <div className="comparison-grid">
        <ComparisonColumn label="Baseline" attachment={baselineAttachment} setAttachment={setBaselineAttachment} result={baseline} running={running === "baseline"} run={() => void execute("baseline", baselineAttachment)} />
        <ComparisonColumn label="Scenario" attachment={scenarioAttachment} setAttachment={setScenarioAttachment} result={scenario} running={running === "scenario"} run={() => void execute("scenario", scenarioAttachment)} />
      </div>
      {!compatible && <section className="run-message run-message--error"><h2>Comparison unavailable</h2><p>The completed responses use different reporting currencies or CT6 schema versions. Both independent results remain preserved.</p></section>}
    </section>
  );
}

function ComparisonColumn({ label, attachment, setAttachment, result, running, run }: { label: string; attachment: string; setAttachment(value: string): void; result: RunResult | null; running: boolean; run(): void }) {
  return <section className="comparison-column" aria-label={`${label} complete run`}><h2>{label}</h2><label>Occurrence attachment<input value={attachment} inputMode="decimal" onChange={(event) => setAttachment(event.target.value)} /></label><button type="button" disabled={running} onClick={run}>{running ? `Running ${label.toLowerCase()}…` : `Run ${label.toLowerCase()}`}</button><ComparisonResult result={result} /></section>;
}

function ComparisonResult({ result }: { result: RunResult | null }) {
  if (!result) return <p className="comparison-empty">No completed run.</p>;
  if (!result.ok) return <div className="comparison-error"><strong>{result.problem?.title ?? "Request is incomplete"}</strong><p>{result.problem?.detail ?? "Correct the declared input and run again."}</p></div>;
  const annual = result.data.post_capacity.annual_rows[0];
  const currency = result.data.request.reporting_currency;
  return <div className="comparison-result"><dl><div><dt>Request ID</dt><dd><code>{result.requestId}</code></dd></div><div><dt>CT4 result hash</dt><dd><code>{result.data.identity.ct4_result_hash}</code></dd></div><div><dt>CT5 result hash</dt><dd><code>{result.data.identity.ct5_result_hash}</code></dd></div>{annual && <><div><dt>Subject loss</dt><dd>{formatCurrency(annual.subject_loss, currency)}</dd></div><div><dt>Gross contractual recovery</dt><dd>{formatCurrency(annual.gross_contractual_recovery, currency)}</dd></div><div><dt>Reinstatement premium payable</dt><dd>{formatCurrency(annual.reinstatement_premium_payable, currency)}</dd></div><div><dt>Net cash settlement</dt><dd>{formatCurrency(annual.net_cash_settlement, currency)}</dd></div><div><dt>Capacity-constrained shortfall</dt><dd>{formatCurrency(annual.capacity_constrained_recovery_shortfall, currency)}</dd></div></>}</dl></div>;
}
