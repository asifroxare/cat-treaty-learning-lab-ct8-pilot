# CT6 Installation and Runtime Guide

## Scope

This package is the backend-only Catastrophe Treaty Learning Lab through CT6.
It exposes the frozen CT2–CT5 engines through a strict FastAPI contract. It is
separate from the Cat XOL Pricing Lab and contains no frontend.

## Windows PowerShell installation

```powershell
Expand-Archive .\cat-treaty-learning-lab-CT6-complete.zip -DestinationPath .\ct6-install
Set-Location .\ct6-install\cat-treaty-learning-lab
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements-dev.txt
python -m pip install -e .
python -m pip check
python -m pytest -q
```

Start the API:

```powershell
Copy-Item .env.example .env
python -m cat_treaty
```

The default address is `http://localhost:8000`. Verify:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:8000/api/v1/capabilities
```

OpenAPI documentation is available at `http://localhost:8000/docs`.

## Production command

```text
uvicorn cat_treaty.api:app --host 0.0.0.0 --port $PORT
```

Set `CT6_CORS_ORIGINS` to a comma-separated allowlist. Wildcard CORS is
rejected. Do not commit `.env`; secrets and deployment policy do not enter
actuarial inputs, outputs or hashes.

## Acceptance gate

Installation is accepted only when `pip check` reports no broken requirements,
the complete pytest suite passes, both health routes return 200, and `git
status --short` is empty for a source checkout.
