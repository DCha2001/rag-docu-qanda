#!/bin/bash
set -e
alembic upgrade e1a2b3c4d5e6
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
