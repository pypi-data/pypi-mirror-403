#!/bin/bash
set -e

# Interactive demo script for paxx
# For CI testing, use: scripts/test-paxx.sh

# Clear any active virtual environment to avoid conflicts with test project's venv
unset VIRTUAL_ENV

# Track directories for cleanup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_PROJECT_DIR="$PROJECT_ROOT/tmp/test-project"

# Cleanup function
cleanup() {
    echo "Stopping services..."
    if [ -d "$TEST_PROJECT_DIR" ]; then
        cd "$TEST_PROJECT_DIR"
        docker compose down 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if Docker is running (macOS-specific: try to start Docker Desktop)
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Starting Docker Desktop..."
    open -a Docker

    # Wait for Docker to start (up to 60 seconds)
    echo "Waiting for Docker to start..."
    for i in {1..60}; do
        if docker info > /dev/null 2>&1; then
            echo "Docker is now running."
            break
        fi
        if [ $i -eq 60 ]; then
            echo "Error: Docker failed to start within 60 seconds."
            exit 1
        fi
        sleep 1
    done
fi

# Run paxx tests first
cd "$PROJECT_ROOT"
uv run pytest tests/

# Bootstrap a test project
echo "=== Bootstrapping test project ==="
mkdir -p tmp
cd tmp
rm -rf test-project
uv run paxx bootstrap test-project

cd test-project
uv sync --all-extras

# Use paxx from parent project's venv directly
PAXX="$PROJECT_ROOT/.venv/bin/paxx"

# Add feature
echo "=== Adding example_products feature ==="
$PAXX feature add example_products

echo "=== Adding auth_aws_cognito feature ==="
$PAXX feature add auth_aws_cognito

python features/auth_aws_cognito/setup.py

# Copy real Cognito settings from project root
sed -i '' '/^COGNITO_/d' .env
grep '^COGNITO_' "$PROJECT_ROOT/.env" >> .env

# Copy CORS settings from project root
sed -i '' '/^CORS_/d' .env
grep '^CORS_' "$PROJECT_ROOT/.env" >> .env

# Start PostgreSQL database (remove old volume to ensure clean state)
echo "=== Starting PostgreSQL ==="
docker compose down -v 2>/dev/null || true

# Check if port 5432 is already in use
if lsof -i :5432 > /dev/null 2>&1; then
    echo -e "\nERROR: Port 5432 is already in use. Stop the existing service first:\n"
    lsof -i :5432
    exit 1
fi

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
$PAXX db status
$PAXX db migrate "add example_products"
$PAXX db upgrade
$PAXX db status

# Test migration down/up cycle
echo "=== Testing migration down/up cycle ==="
$PAXX db downgrade
$PAXX db status
$PAXX db upgrade
$PAXX db status

# Test feature removal and re-add
echo "=== Testing feature removal and re-add ==="
rm -rf features/example_products
$PAXX feature add example_products
$PAXX feature create test_feature

# Open browser and start interactive server
echo "=== Starting interactive server ==="
open http://127.0.0.1:8000/docs
$PAXX start
