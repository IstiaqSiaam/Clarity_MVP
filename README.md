# Clarity MVP

Monorepo for the journaling + analytics MVP.

## Structure

- apps/web: Next.js frontend
- apps/api: FastAPI backend gateway (auth, user, journal, payment)
- apps/nlp_service: NLP workers (sentiment, themes, embeddings)
- libs/contracts: OpenAPI/AsyncAPI specs
- infra: Docker Compose, Helm and Terraform
- scripts: seeds & local tooling

## Quickstart

1. Copy `.env.example` to `.env` and fill values
2. `docker compose -f infra/docker-compose.yml up --build`
3. Open http://localhost:3000 (web) and http://localhost:8000/health (api)
