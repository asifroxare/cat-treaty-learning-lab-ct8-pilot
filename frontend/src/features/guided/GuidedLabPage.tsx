import { useMemo, useState } from "react";

import { createCT6Client, type CT6Client, type RunResult } from "../../api/client";
import { guidedExperiments, type GuidedExperiment, type GuidedRequest } from "../../scenarios/guided";
import { resolveEvidence } from "../../scenarios/evidence";
import "./GuidedLabPage.css";

export function GuidedLabPage({ client: suppliedClient }: { client?: CT6Client }) {
  const client = useMemo(() => suppliedClient ?? createCT6Client(), [suppliedClient]);
  const [selectedId, setSelectedId] = useState("E01");
  const [prediction, setPrediction] = useState("");
  const [baseline, setBaseline] = useState<RunResult | null>(null);
  const [scenario, setScenario] = useState<RunResult | null>(null);
  const [running, setRunning] = useState<"baseline" | "scenario" | null>(null);
  const experiment = guidedExperiments.find((item) => item.id === selectedId) ?? guidedExperiments[0]!;

  const choose = (id: string) => { setSelectedId(id); setPrediction(""); setBaseline(null); setScenario(null); };
  const run = async (kind: "baseline" | "scenario", source: GuidedRequest) => {
    setRunning(kind);
    const result = source.mode === "catalogue"
      ? await client.runCatalogue(structuredClone(source.request))
      : await client.runHoursClause(structuredClone(source.request));
    if (kind === "baseline") setBaseline(result); else setScenario(result);
    setRunning(null);
  };
  const predictionRecorded = prediction.trim().length > 0;
  const canRenderTakeaway = baseline?.ok && scenario?.ok
    && resolveEvidence(baseline.data, experiment.takeaway)
    && resolveEvidence(scenario.data, experiment.takeaway);

  return (
    <section className="guided-page" aria-labelledby="guided-title">
      <header><p className="page-eyebrow">Guided Lab</p><h1 id="guided-title">Learn one treaty mechanism at a time</h1><p className="page-lede">Predict first, run two complete CT6 requests, then inspect returned evidence. Free-text predictions are recorded for reflection and are not graded.</p></header>
      <nav className="experiment-tabs" aria-label="Guided experiments">{guidedExperiments.map((item) => <button type="button" aria-current={item.id === experiment.id ? "page" : undefined} onClick={() => choose(item.id)} key={item.id}><span>{item.id}</span>{item.title}</button>)}</nav>
      <article className="experiment-workspace">
        <header className="experiment-heading"><div><p className="result-kicker">{experiment.id} · {experiment.learnerLevel} · fixture {experiment.version}</p><h2>{experiment.title}</h2><p>{experiment.objective}</p></div><div className="controlled-change"><strong>Controlled input change</strong>{experiment.controlledFields.map((field) => <code key={field}>{field}</code>)}</div></header>
        <label className="prediction-box" htmlFor="prediction"><strong>Prediction prompt</strong><span>{experiment.predictionPrompt}</span><textarea id="prediction" value={prediction} onChange={(event) => setPrediction(event.target.value)} rows={3} placeholder="Record your prediction before running…" /></label>
        <div className="guided-actions"><button type="button" disabled={!predictionRecorded || running !== null} onClick={() => void run("baseline", experiment.baseline)}>{running === "baseline" ? "Running baseline…" : "Run baseline"}</button><button type="button" disabled={!predictionRecorded || running !== null} onClick={() => void run("scenario", experiment.scenario)}>{running === "scenario" ? "Running scenario…" : "Run controlled scenario"}</button></div>
        {!predictionRecorded && <p className="prediction-gate">Record a prediction to enable both runs.</p>}
        <div className="guided-results"><GuidedRunCard label="Baseline" result={baseline} /><GuidedRunCard label="Controlled scenario" result={scenario} /></div>
        {baseline && scenario && !canRenderTakeaway && baseline.ok && scenario.ok && <div className="run-message run-message--error"><h3>Evidence contract incomplete</h3><p>The result-specific takeaway is withheld because one or more evidence paths did not resolve.</p></div>}
        {canRenderTakeaway && <section className="takeaway" aria-labelledby="takeaway-title"><p className="result-kicker">Evidence-backed takeaway</p><h3 id="takeaway-title">What to carry forward</h3><p>{experiment.takeaway.statement}</p><p><strong>Inspect next:</strong> {experiment.inspectNext}</p><details><summary>Resolved evidence paths</summary><ul>{experiment.takeaway.evidencePaths.map((path) => <li key={path}><code>{path}</code></li>)}</ul></details></section>}
      </article>
    </section>
  );
}

function GuidedRunCard({ label, result }: { label: string; result: RunResult | null }) {
  if (!result) return <section className="guided-run-card guided-run-card--empty"><h3>{label}</h3><p>Not run yet.</p></section>;
  if (!result.ok) return <section className="guided-run-card guided-run-card--error"><h3>{label}</h3><p>{result.problem?.title ?? "Run unavailable"}</p><p>{result.problem?.detail ?? "No result was fabricated."}</p></section>;
  return <section className="guided-run-card"><h3>{label}</h3><dl><div><dt>Request ID</dt><dd><code>{result.requestId}</code></dd></div><div><dt>CT4 result hash</dt><dd><code>{result.data.identity.ct4_result_hash}</code></dd></div><div><dt>CT5 result hash</dt><dd><code>{result.data.identity.ct5_result_hash}</code></dd></div></dl>{result.data.warnings.length > 0 && <><h4>Warnings</h4><ul>{result.data.warnings.map((warning, index) => <li key={`${warning.code}-${index}`}>{warning.code}: {warning.message}</li>)}</ul></>}<h4>Returned learning facts</h4><ul>{result.data.learning.facts.map((fact, index) => <li key={`${fact.metric_name}-${index}`}><strong>{fact.metric_name}</strong>: {fact.driver_statement} <small>Trace: {fact.trace_references.join(", ")}</small></li>)}</ul></section>;
}
