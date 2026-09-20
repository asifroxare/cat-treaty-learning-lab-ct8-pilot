import { Link } from "react-router-dom";

import "./HomePage.css";

const pathways = [
  ["/guided", "Guided Lab", "Learn through controlled, evidence-backed experiments."],
  ["/explore", "Explore Treaty", "Build catalogue-mode inputs and inspect the full result hierarchy."],
  ["/hours-clause", "Hours-Clause Lab", "Examine admissibility before contractual election."],
] as const;

export function HomePage() {
  return (
    <div className="home-page">
      <section className="hero" aria-labelledby="home-title">
        <p className="hero-kicker">Treaty mechanics, made inspectable</p>
        <h1 id="home-title">See what happened.<br />Understand why.</h1>
        <p className="hero-summary">
          Explore catastrophe treaty loss stages, program geometry, annual capacity,
          reinstatements and occurrence elections through authoritative CT6 evidence.
        </p>
        <div className="scope-banner">
          <strong>This is a treaty learning lab—not the Cat XOL Pricing Learning Lab.</strong>
          <span>It does not calculate technical premium or estimate real catastrophe risk.</span>
        </div>
      </section>

      <section className="pathway-section" aria-labelledby="choose-path">
        <div>
          <p className="section-number">01 / Start</p>
          <h2 id="choose-path">Choose how you want to learn</h2>
        </div>
        <div className="pathway-grid">
          {pathways.map(([to, title, description], index) => (
            <Link className="pathway-card" to={to} key={to}>
              <span className="pathway-index">0{index + 1}</span>
              <h3>{title}</h3>
              <p>{description}</p>
              <span className="pathway-action" aria-hidden="true">Open →</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="authority-strip" aria-label="Calculation authority">
        <p>Frontend role</p>
        <strong>Explain and visualize</strong>
        <span aria-hidden="true">→</span>
        <p>CT6 backend role</p>
        <strong>Calculate and reconcile</strong>
      </section>
    </div>
  );
}
