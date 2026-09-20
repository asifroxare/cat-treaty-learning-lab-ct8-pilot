# CT7 Installation, Reproduction and Runtime Guide

## Scope

This package contains the Catastrophe Treaty Learning Lab through CT7:

- frozen CT1–CT5 treaty engines;
- CT6 FastAPI orchestration and authoritative response contract; and
- CT7 React learning, comparison, hours-clause and audit experience.

It remains a separate product from the Cat XOL Pricing Learning Lab. The
frontend contains no actuarial calculations.

## Windows PowerShell installation

Extract the final ZIP into `C:\\Aasif\\Cat XOL`. The resulting project folder
must be `C:\\Aasif\\Cat XOL\\cat-treaty-learning-lab`.

Open PowerShell in that folder and run:

```powershell
py -3.14 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r .\\requirements-dev.txt
python -m pip install -e .
python -m pip check
python -m pytest -q

Set-Location .\\frontend
npm ci
npm run check
$env:PYTHON = (Resolve-Path ..\\.venv\\Scripts\\python.exe).Path
npm run test:real-api
Set-Location ..
```

Expected evidence is `No broken requirements found`, `1003 passed`, all
frontend gates passing, and successful live catalogue and hours-clause runs.
The same checks can be launched from the repository root with:

```powershell
py -3.14 .\\scripts\\reproduce_release.py
```

## Start the lab

Use two PowerShell terminals.

Terminal 1 — API:

```powershell
Set-Location 'C:\\Aasif\\Cat XOL\\cat-treaty-learning-lab'
.\\.venv\\Scripts\\Activate.ps1
Copy-Item .env.example .env -ErrorAction SilentlyContinue
python -m cat_treaty
```

Terminal 2 — frontend:

```powershell
Set-Location 'C:\\Aasif\\Cat XOL\\cat-treaty-learning-lab\\frontend'
npm run dev
```

Open `http://localhost:5173`. API documentation is at
`http://localhost:8000/docs`.

## Runtime configuration

The frontend defaults to `http://localhost:8000`. Use
`frontend/.env.local` only when an explicit alternative is required:

```text
VITE_CT6_API_BASE_URL=http://localhost:8000
```

For production, use:

```text
uvicorn cat_treaty.api:app --host 0.0.0.0 --port $PORT
```

Set `CT6_CORS_ORIGINS` to an explicit comma-separated allowlist. Wildcard CORS
is rejected. Never commit `.env` files.

## Deferred deployment gates

CT7 completion does not authorize public deployment. Physical Chrome, Edge,
Firefox and mobile-width browser testing, hosting security configuration and
deployment smoke tests remain part of deployment readiness.
