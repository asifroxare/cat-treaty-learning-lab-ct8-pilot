# CT7 Frontend

This directory contains the Catastrophe Treaty Learning Lab frontend. CT6 is
the sole actuarial authority; React explains and visualizes returned evidence.

## Development

Activate the repository Python environment first so the OpenAPI drift check can
import CT6, then run:

```text
npm install
npm run check
npm run dev
```

The development API defaults to `http://localhost:8000`. Copy `.env.example`
to `.env.local` only when an explicit alternative is required.

## Contract generation

`openapi/ct6.openapi.json` is exported from the frozen FastAPI application.
`src/api/generated/ct6.ts` is generated from that snapshot. Do not edit either
file manually and do not regenerate after backend drift without compatibility
review.
