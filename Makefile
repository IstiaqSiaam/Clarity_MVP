up:
docker compose -f infra/docker-compose.yml up --build

down:
docker compose -f infra/docker-compose.yml down -v

fmt:
pnpm format

seed:
python scripts/seed.py
