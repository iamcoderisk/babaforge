#!/bin/bash
set -e

echo "🧪 Running tests..."

source venv/bin/activate

# Unit tests
echo "Running unit tests..."
pytest tests/unit -v --cov=app --cov-report=html

# Integration tests
echo "Running integration tests..."
pytest tests/integration -v

echo "✅ All tests passed!"