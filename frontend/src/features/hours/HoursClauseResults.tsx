import type { AuthoritativeSuccessResponse } from "../../api/authoritative";
import type { ResultFreshness } from "../../api/runState";
import { formatCurrency, formatNumber } from "../../formatting/authoritative";
import { CatalogueResults } from "../results/CatalogueResults";

export function HoursClauseResults({ data, freshness }: { data: AuthoritativeSuccessResponse; freshness: ResultFreshness }) {
  const currency = data.request.reporting_currency;
  return (
    <div className="catalogue-results">
      <section className="result-panel" aria-labelledby="election-title">
        <p className="result-kicker">Occurrence election</p>
        <h2 id="election-title">Candidate admissibility precedes election</h2>
        <dl className="summary-grid">
          <div><dt>Selected method</dt><dd>{data.pre_capacity.selected_election_method?.replaceAll("_", " ") ?? "None"}</dd></div>
          <div><dt>Selected candidate set</dt><dd>{data.pre_capacity.selected_candidate_set_id ?? "None"}</dd></div>
          <div><dt>Valid candidate sets</dt><dd>{data.pre_capacity.valid_candidate_set_ids.join(", ") || "None"}</dd></div>
        </dl>
      </section>

      <section className="result-panel table-panel" aria-labelledby="windows-title">
        <h2 id="windows-title">Candidate windows</h2>
        <div className="table-scroll"><table><thead><tr><th>Window</th><th>Time</th><th>Components</th><th>Subject loss</th><th>Admissibility</th><th>Exclusion evidence</th></tr></thead><tbody>
          {data.pre_capacity.candidate_windows.map((window) => <tr key={window.candidate_id}><td>{window.candidate_id}</td><td>{formatNumber(window.start)}–{formatNumber(window.end)}</td><td>{window.component_ids.join(", ")}</td><td>{formatCurrency(window.subject_loss, currency)}</td><td>{window.admissibility}</td><td>{evidence(window.exclusion_codes, window.exclusion_reasons, window.affected_ids)}</td></tr>)}
        </tbody></table></div>
      </section>

      <section className="result-panel table-panel" aria-labelledby="sets-title">
        <h2 id="sets-title">Candidate sets and contractual eligibility</h2>
        <div className="table-scroll"><table><thead><tr><th>Set</th><th>Windows</th><th>Subject loss</th><th>Contractual recovery</th><th>Admissibility</th><th>Exclusion evidence</th></tr></thead><tbody>
          {data.pre_capacity.candidate_sets.map((set) => <tr key={set.candidate_set_id}><td>{set.candidate_set_id}</td><td>{set.window_ids.join(", ")}</td><td>{formatCurrency(set.total_subject_loss, currency)}</td><td>{set.total_contractual_recovery == null ? "Not calculated for excluded set" : formatCurrency(set.total_contractual_recovery, currency)}</td><td>{set.admissibility}</td><td>{evidence(set.exclusion_codes, set.exclusion_reasons, set.affected_ids)}</td></tr>)}
        </tbody></table></div>
        <p className="evidence-note">Excluded candidates remain visible for learning and audit, but CT6 never admits them into contractual election.</p>
      </section>

      <CatalogueResults data={data} freshness={freshness} />
    </div>
  );
}

function evidence(codes: readonly string[], reasons: readonly string[], affected: readonly string[]) {
  if (!codes.length && !reasons.length) return "Eligible — no exclusion recorded";
  return <ul className="evidence-list">{codes.map((code, index) => <li key={`${code}-${index}`}><strong>{code}</strong>{reasons[index] ? ` — ${reasons[index]}` : ""}{affected.length ? ` · affected: ${affected.join(", ")}` : ""}</li>)}</ul>;
}
