import type { AuthoritativeSuccessResponse } from "../../api/authoritative";
import type { ResultFreshness } from "../../api/runState";
import { formatCurrency, formatInteger, formatNumber, formatPercent } from "../../formatting/authoritative";
import { asCssPixels, recoveryBarGeometry } from "../../visualization/geometry/recoveryBars";
import { tailPointGeometry } from "../../visualization/geometry/tailPlot";
import { subjectOepPoints } from "./tailSeries";
import "./CatalogueResults.css";

interface CatalogueResultsProps {
  data: AuthoritativeSuccessResponse;
  freshness: ResultFreshness;
}

export function CatalogueResults({ data, freshness }: CatalogueResultsProps) {
  const currency = data.request.reporting_currency;
  const preAnnual = data.pre_capacity.annual_rows[0];
  const postAnnual = data.post_capacity.annual_rows[0];
  const geometry = preAnnual && postAnnual
    ? recoveryBarGeometry(preAnnual.subject_loss, preAnnual.gross_contractual_recovery_pre_annual_capacity, postAnnual.gross_contractual_recovery)
    : null;
  const tailPoints = subjectOepPoints(data.pre_capacity.tail_analytics);
  const tailMaximum = tailPoints[0]?.loss;

  return (
    <div className="catalogue-results" aria-label={freshness === "stale" ? "Stale prior authoritative result" : "Current authoritative result"}>
      <section className="result-panel result-summary" aria-labelledby="result-summary-title">
        <div>
          <p className="result-kicker">Completion and scope</p>
          <h2 id="result-summary-title">{data.api.completion_status}</h2>
        </div>
        <dl className="summary-grid">
          <div><dt>Simulation</dt><dd>{data.request.simulation_id}</dd></div>
          <div><dt>Program</dt><dd>{data.request.program_id}</dd></div>
          <div><dt>Trials</dt><dd>{formatInteger(data.request.trial_count)}</dd></div>
          <div><dt>Occurrences</dt><dd>{formatInteger(data.request.occurrence_count)}</dd></div>
          <div><dt>Detail</dt><dd>{data.request.response_detail}</dd></div>
          <div><dt>Currency</dt><dd>{currency}</dd></div>
        </dl>
      </section>

      {data.warnings.length > 0 && (
        <section className="result-panel warning-panel" aria-labelledby="warnings-title">
          <h2 id="warnings-title">Warnings</h2>
          <ul>{data.warnings.map((warning, index) => <li key={`${warning.code}-${index}`}><strong>{warning.code}</strong> — {warning.message}{warning.return_period != null && <> (return period {formatNumber(warning.return_period)})</>}</li>)}</ul>
        </section>
      )}

      {preAnnual && postAnnual && (
        <>
          <section className="result-panel" aria-labelledby="recovery-title">
            <p className="result-kicker">Pre-annual-capacity entitlement</p>
            <h2 id="recovery-title">Subject loss and recovery flow</h2>
            <div className="metric-grid">
              <Metric label="Subject loss" value={formatCurrency(preAnnual.subject_loss, currency)} />
              <Metric label="Gross contractual recovery pre annual capacity" value={formatCurrency(preAnnual.gross_contractual_recovery_pre_annual_capacity, currency)} />
              <Metric label="Insurer net loss pre annual capacity" value={formatCurrency(preAnnual.insurer_net_loss_pre_annual_capacity, currency)} />
              <Metric label="Maximum occurrence recovery" value={formatCurrency(preAnnual.maximum_occurrence_recovery_pre_annual_capacity, currency)} />
            </div>
            {geometry && (
              <div className="recovery-bars" role="img" aria-label="Proportional comparison of authoritative subject loss, pre-capacity recovery and post-capacity recovery. Exact values appear in the adjacent metrics.">
                <RecoveryBar label="Subject loss" width={asCssPixels(geometry.subjectLossWidth)} tone="subject" />
                <RecoveryBar label="Pre-capacity" width={asCssPixels(geometry.preCapacityWidth)} tone="pre" />
                <RecoveryBar label="Post-capacity" width={asCssPixels(geometry.postCapacityWidth)} tone="post" />
              </div>
            )}
          </section>

          <section className="result-panel" aria-labelledby="settlement-title">
            <p className="result-kicker">Post-capacity settlement</p>
            <h2 id="settlement-title">Recovery, premium and cash remain separate</h2>
            <div className="metric-grid settlement-grid">
              <Metric label="Gross contractual recovery" value={formatCurrency(postAnnual.gross_contractual_recovery, currency)} />
              <Metric label="Reinstatement premium payable" value={formatCurrency(postAnnual.reinstatement_premium_payable, currency)} />
              <Metric label="Net cash settlement" value={formatCurrency(postAnnual.net_cash_settlement, currency)} />
              <Metric label="Capacity-constrained shortfall" value={formatCurrency(postAnnual.capacity_constrained_recovery_shortfall, currency)} />
              <Metric label="Insurer net subject loss" value={formatCurrency(postAnnual.insurer_net_subject_loss, currency)} />
              <Metric label="Maximum occurrence recovery" value={formatCurrency(postAnnual.maximum_occurrence_recovery, currency)} />
            </div>
          </section>
        </>
      )}

      {postAnnual?.layer_summaries.map((layer) => (
        <section className="result-panel" aria-labelledby={`capacity-${layer.layer_id}`} key={layer.layer_id}>
          <p className="result-kicker">Annual capacity · {layer.layer_id}</p>
          <h2 id={`capacity-${layer.layer_id}`}>Capacity and reinstatement ledger</h2>
          <div className="metric-grid">
            <Metric label="Initial active capacity" value={formatCurrency(layer.initial_capacity, currency)} />
            <Metric label="Final active capacity" value={formatCurrency(layer.final_active_capacity, currency)} />
            <Metric label="Total recovery" value={formatCurrency(layer.total_recovery, currency)} />
            <Metric label="Amount reinstated" value={formatCurrency(layer.total_reinstated, currency)} />
            <Metric label="Capacity utilization" value={layer.realized_capacity_utilization == null ? "N/A – no payable capacity" : formatPercent(layer.realized_capacity_utilization)} detail={layer.realized_capacity_utilization_status} />
            <Metric label="Reinstatement reserve utilization" value={layer.reinstatement_reserve_utilization == null ? "N/A – no reinstatement reserve" : formatPercent(layer.reinstatement_reserve_utilization)} detail={layer.reinstatement_reserve_utilization_status} />
          </div>
        </section>
      ))}

      <OccurrenceTable data={data} currency={currency} />

      {tailMaximum != null && tailPoints.length > 0 && (
        <section className="result-panel table-panel" aria-labelledby="tail-title">
          <p className="result-kicker">Empirical points returned by CT6</p>
          <h2 id="tail-title">Subject-loss OEP curve</h2>
          <svg viewBox="0 0 100 100" role="img" aria-label="Subject-loss occurrence exceedance curve. Exact authoritative points follow in the table.">
            {tailPoints.map((point) => {
              const plotted = tailPointGeometry(point.exceedanceProbability, point.loss, tailMaximum);
              return <circle key={point.rank} cx={plotted.x} cy={plotted.y} r="1.5" />;
            })}
          </svg>
          <div className="table-scroll"><table>
            <caption>Authoritative OEP points without interpolation or rebucketing</caption>
            <thead><tr><th>Rank</th><th>Exceedance probability</th><th>Loss</th></tr></thead>
            <tbody>{tailPoints.map((point) => <tr key={point.rank}><td>{formatInteger(point.rank)}</td><td>{formatPercent(point.exceedanceProbability)}</td><td>{formatCurrency(point.loss, currency)}</td></tr>)}</tbody>
          </table></div>
        </section>
      )}

      <section className="result-panel" aria-labelledby="learning-title">
        <p className="result-kicker">Structured learning facts</p>
        <h2 id="learning-title">What the authoritative engine reports</h2>
        {data.learning.facts.length === 0 ? <p>No learning facts were returned.</p> : (
          <ul className="fact-list">{data.learning.facts.map((fact, index) => (
            <li key={`${fact.metric_name}-${index}`}>
              <strong>{fact.metric_name}</strong>
              <span>{fact.driver_statement}</span><span>{fact.meaning}</span>
              {fact.value != null && <span>Authoritative value: {formatNumber(fact.value)}</span>}
              <small>Trace: {fact.trace_references.join(", ")}</small>
            </li>
          ))}</ul>
        )}
      </section>

      <section className="result-panel audit-panel" aria-labelledby="audit-title">
        <p className="result-kicker">Audit trail</p>
        <h2 id="audit-title">Versions, hashes and reconciliations</h2>
        <dl className="audit-grid">
          <Audit label="Request ID" value={data.api.request_id} />
          <Audit label="CT4 input hash" value={data.identity.ct4_input_hash} />
          <Audit label="CT4 result hash" value={data.identity.ct4_result_hash} />
          <Audit label="CT5 input hash" value={data.identity.ct5_input_hash} />
          <Audit label="CT5 result hash" value={data.identity.ct5_result_hash} />
          <Audit label="CT2 engine/schema" value={`${data.versions.ct2_engine_version} / ${data.versions.ct2_schema_version}`} />
          <Audit label="CT3 engine/schema" value={`${data.versions.ct3_engine_version} / ${data.versions.ct3_schema_version}`} />
          <Audit label="CT4 engine/schema" value={`${data.versions.ct4_engine_version} / ${data.versions.ct4_schema_version}`} />
          <Audit label="CT5 engine/schema" value={`${data.versions.ct5_engine_version} / ${data.versions.ct5_schema_version}`} />
          <Audit label="CT6 API/schema" value={`${data.versions.ct6_api_version} / ${data.versions.ct6_schema_version}`} />
        </dl>
        <table>
          <caption>Authoritative reconciliations</caption>
          <thead><tr><th>Scope</th><th>Identifier</th><th>Formula references</th><th>Status</th></tr></thead>
          <tbody>{data.learning.reconciliations.map((item) => <tr key={`${item.scope}-${item.identifier}`}><td>{item.scope}</td><td>{item.identifier}</td><td>{item.formula_references.join(", ")}</td><td>{item.passed ? "Passed" : "Failed"}</td></tr>)}</tbody>
        </table>
      </section>
    </div>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong>{detail && <small>{detail.replaceAll("_", " ")}</small>}</div>;
}

function RecoveryBar({ label, width, tone }: { label: string; width: string; tone: string }) {
  return <div className="bar-row"><span>{label}</span><div className="bar-track"><span className={`bar-fill bar-fill--${tone}`} style={{ width }} /></div></div>;
}

function Audit({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd><code>{value}</code></dd></div>;
}

function OccurrenceTable({ data, currency }: { data: AuthoritativeSuccessResponse; currency: string }) {
  const rows = data.post_capacity.occurrence_rows;
  if (rows == null) return <section className="result-panel"><h2>Occurrence ledger</h2><p>Occurrence rows were omitted by the requested summary response. Identity, analytics and audit evidence remain authoritative.</p></section>;
  return (
    <section className="result-panel table-panel" aria-labelledby="occurrence-title">
      <h2 id="occurrence-title">Post-capacity occurrence ledger</h2>
      <div className="table-scroll"><table><thead><tr><th>Trial</th><th>Event</th><th>Subject loss</th><th>Pre-capacity entitlement</th><th>Gross recovery</th><th>Premium payable</th><th>Net cash</th><th>Reconciled</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={`${row.annual_trial_id}-${row.occurrence_sequence}-${row.event_id}`}><td>{formatInteger(row.annual_trial_id)}</td><td>{row.event_id}</td><td>{formatCurrency(row.subject_loss, currency)}</td><td>{formatCurrency(row.gross_contractual_recovery_pre_annual_capacity, currency)}</td><td>{formatCurrency(row.gross_contractual_recovery, currency)}</td><td>{formatCurrency(row.reinstatement_premium_payable, currency)}</td><td>{formatCurrency(row.net_cash_settlement, currency)}</td><td>{row.reconciliation_passed ? "Yes" : "No"}</td></tr>)}</tbody></table></div>
    </section>
  );
}
