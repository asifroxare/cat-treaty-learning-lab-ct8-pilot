import { Link } from "react-router-dom";

import { useCatalogueRun } from "../explore/useCatalogueRun";

export function AuditTrailPage() {
  const run = useCatalogueRun();
  const data = run.priorSuccess?.data;
  return (
    <section className="foundation-page" aria-labelledby="audit-page-title">
      <p className="page-eyebrow">Audit Trail</p>
      <h1 id="audit-page-title">Follow every authoritative identity</h1>
      <p className="page-lede">This route preserves the latest catalogue run while you move through the learning lab.</p>
      {!data ? (
        <div className="checkpoint-note"><p className="checkpoint-label">No completed catalogue run</p><p>Complete a scenario in <Link to="/explore">Explore Treaty</Link> to populate its request ID, hashes, versions and reconciliation evidence.</p></div>
      ) : (
        <div className="result-panel audit-panel">
          <p className="result-kicker">{run.freshness === "stale" ? "Previous result — inputs changed" : "Current authoritative result"}</p>
          <h2>Deterministic run identity</h2>
          <dl className="audit-grid">
            <Audit label="Request ID" value={data.api.request_id} />
            <Audit label="Simulation ID" value={data.identity.simulation_id} />
            <Audit label="CT4 input hash" value={data.identity.ct4_input_hash} />
            <Audit label="CT4 result hash" value={data.identity.ct4_result_hash} />
            <Audit label="CT5 input hash" value={data.identity.ct5_input_hash} />
            <Audit label="CT5 result hash" value={data.identity.ct5_result_hash} />
          </dl>
          <h2>Reconciliation evidence</h2>
          <table><thead><tr><th>Scope</th><th>Identifier</th><th>References</th><th>Status</th></tr></thead><tbody>
            {data.learning.reconciliations.map((item) => <tr key={`${item.scope}-${item.identifier}`}><td>{item.scope}</td><td>{item.identifier}</td><td>{item.formula_references.join(", ")}</td><td>{item.passed ? "Passed" : "Failed"}</td></tr>)}
          </tbody></table>
        </div>
      )}
    </section>
  );
}

function Audit({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd><code>{value}</code></dd></div>;
}
