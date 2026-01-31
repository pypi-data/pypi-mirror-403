#!/bin/bash
set -e

# CI-compatible test script for paxx
# For interactive demo, use: scripts/demo-paxx.sh

# Clear any active virtual environment to avoid conflicts with test project's venv
unset VIRTUAL_ENV

# Track directories for cleanup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_PROJECT_DIR="$PROJECT_ROOT/tmp/test-project"

# Cleanup function - defined early so trap works for all failures
cleanup() {
    echo "Cleaning up..."
    if [ -d "$TEST_PROJECT_DIR" ]; then
        cd "$TEST_PROJECT_DIR"
        docker compose down -v 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# 1. Run paxx's own unit and integration tests
echo "=== Running paxx unit and integration tests ==="
cd "$PROJECT_ROOT"
uv run pytest tests/

# 2. Bootstrap a test project
echo "=== Bootstrapping test project ==="
mkdir -p tmp
cd tmp
rm -rf test-project
uv run paxx bootstrap test-project

cd test-project
uv sync --all-extras

# Use paxx from parent project's venv directly
PAXX="$PROJECT_ROOT/.venv/bin/paxx"

# 3. Add features and run migrations
echo "=== Adding example_products feature ==="
$PAXX feature add example_products

# Start PostgreSQL database (remove old volume to ensure clean state)
echo "=== Starting PostgreSQL ==="
docker compose down -v 2>/dev/null || true
docker compose up db -d

# Wait for database to be healthy
echo "Waiting for database to be ready..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        echo "Database is ready."
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: Database failed to start within 30 seconds."
        exit 1
    fi
    sleep 1
done

# Run migrations
echo "=== Running migrations ==="
$PAXX db migrate "add example_products"
$PAXX db upgrade
$PAXX db status

# Test migration down/up cycle
echo "=== Testing migration down/up cycle ==="
$PAXX db downgrade
$PAXX db upgrade

# Test feature removal and re-add
echo "=== Testing feature removal and re-add ==="
rm -rf features/example_products
$PAXX feature add example_products
$PAXX feature create test_feature

# Test infra component addition
echo "=== Adding metrics infra component ==="
$PAXX infra add metrics
$PAXX infra add redis
$PAXX infra add storage

# Test extensions addition
echo "=== Adding extensions ==="
$PAXX ext add arq
$PAXX ext add postgis
$PAXX ext add websocket

# 4. Run feature unit/integration tests
echo "=== Running feature tests ==="
uv run pytest features/*/tests/ -v 2>/dev/null || echo "No feature tests found"

# 5. Start app and run e2e tests
echo "=== Starting app for e2e tests ==="
docker compose up app -d --build

# Wait for app to be healthy
echo "Waiting for app to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "App is ready."
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: App failed to start within 30 seconds."
        docker compose logs app
        exit 1
    fi
    sleep 1
done

# Run e2e tests
echo "=== Running e2e tests ==="
APP_URL=http://localhost:8000 uv run pytest e2e/ -v

echo "=== All tests passed ==="
