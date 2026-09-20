import { NavLink, Outlet } from "react-router-dom";

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
  return (
    <div className="app-shell">
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

      <main id="main-content" className="main-content">
        <Outlet />
      </main>

      <footer className="site-footer">
        <p><strong>Educational use only.</strong> Not a commercial catastrophe model or professional advice.</p>
        <p>Authoritative calculations are produced exclusively by the CT6 Python backend.</p>
      </footer>
    </div>
  );
}
