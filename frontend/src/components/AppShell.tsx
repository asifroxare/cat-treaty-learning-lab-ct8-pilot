import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { CT8_NOCARD_MODE, CT8_PILOT_MODE } from "../api/config";
import { loadPilotLimits } from "../api/pilotCapabilities";

import "./AppShell.css";

const navigation = [
  ["/", "Start"],
  ["/guided", "Guided Lab"],
  ["/explore", "Explore Treaty"],
  ["/hours-clause", "Hours-Clause Lab"],
  ["/compare", "Compare"],
  ["/audit", "Audit Trail"],
] as const;

export function AppShell() {
  const [pilotLimits, setPilotLimits] = useState<string | null>(null);
  useEffect(() => {
    if (!CT8_PILOT_MODE) return;
    const controller = new AbortController();
    void loadPilotLimits(controller.signal).then((limits) => {
      if (!controller.signal.aborted) setPilotLimits(limits);
    });
    return () => controller.abort();
  }, []);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">E</span>
          <div>
            <p className="brand-owner">EdInsured</p>
            <p className="brand-product">Catastrophe Treaty Learning Lab</p>
          </div>
        </div>
        <div className="engine-badge" aria-label="CT6 backend contract">
          <span className="engine-dot" aria-hidden="true" />
          CT6 contract
        </div>
      </header>

      {CT8_PILOT_MODE && <p role="status" className="scope-banner">
        <strong>Invited test release.</strong> Only measured pilot scenarios are available.
        {pilotLimits ? ` ${pilotLimits}` : " Limits are unavailable; check access before running a scenario."}
        {" "}Full CT6 capacity is deferred; the Python backend rejects out-of-scope requests.
        {CT8_NOCARD_MODE && <> {" "}<a href="/auth/start">Sign in with GitHub</a></>}
      </p>}

      <nav className="primary-nav" aria-label="Primary navigation">
        {navigation.map(([to, label]) => (
          <NavLink
            key={to}
            end={to === "/"}
            to={to}
            className={({ isActive }) => isActive ? "nav-link nav-link-active" : "nav-link"}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <main id="main-content" className="main-content" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="site-footer">
        <p><strong>Educational use only.</strong> Not a commercial catastrophe model or professional advice.</p>
        <p>Authoritative calculations are produced exclusively by the CT6 Python backend.</p>
      </footer>
    </div>
  );
}
