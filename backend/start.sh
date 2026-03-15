#!/bin/sh
set -e

echo "=== Axelo Backend Starting ==="
echo "DATABASE_URL: $DATABASE_URL"

echo "--- Creating tables ---"
python -c "
from app.database import Base, engine
import app.models
Base.metadata.create_all(bind=engine)
print('Tables OK')
"

echo "--- Running Alembic migrations ---"
alembic upgrade head || echo "Alembic migration warning (may be OK on first run)"

echo "--- Seeding data ---"
python -c "
from app.seed import seed
seed()
"

echo "--- Starting uvicorn ---"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
