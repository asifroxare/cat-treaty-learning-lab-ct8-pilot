# CT0 Independent Reproduction Gate

**Project:** Catastrophe Treaty Learning Lab  
**Gate date:** 11 September 2026  
**Gate status:** PASS  
**Purpose:** Verify the supplied Cat XOL Pricing Simulator before authorizing CT1 development.

## Source identity

- Archive: `cat-xol-pricing-lab.zip`
- SHA-256: `2472550B18AE3F522D0740F35E187DF9E16377B9BD50B6F331FBB6087680A6C9`
- Git branch: `main`
- Git commit: `a47eb24605f56e1c85701e04ee12101171a9c881`
- Commit timestamp: `2026-09-09T09:09:53+05:30`
- Commit subject: `Complete C12 deployment readiness and production configuration`
- Initial working tree: clean

## Backend reproduction

Fresh Windows virtual environment:

- Python: `3.14.6`
- NumPy: `2.5.3`
- pytest: `9.1.1`
- FastAPI: `0.141.1`
- Pydantic: `2.13.5`
- Uvicorn: `0.52.4`
- httpx: `0.28.1`
- Dependency check: no broken requirements

Result:

```text
154 passed, 2 warnings in 2.39s