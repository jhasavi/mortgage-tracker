#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Mortgage Tracker Smoke Test"
echo "================================"
echo ""
echo "Environment:"
echo "  PWD: $(pwd)"
echo "  Python: $(python3 --version 2>&1 || python --version 2>&1 || echo 'Python not found')"
echo ""

# Ensure env vars exist (do not print secrets)
if [ -z "${SUPABASE_URL:-}" ]; then
  echo "❌ SUPABASE_URL is not set"
  exit 1
fi

if [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "❌ SUPABASE_SERVICE_ROLE_KEY is not set"
  exit 1
fi

echo "✅ Environment variables verified"
echo ""

# If you use src/ layout, ensure imports work
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"
echo "  PYTHONPATH: $PYTHONPATH"
echo ""

# Show key files
echo "Files:"
if [ -f "sources.yaml" ]; then
  echo "  ✅ sources.yaml exists"
else
  echo "  ❌ sources.yaml NOT FOUND"
  exit 1
fi

if [ -d "src/mortgage_tracker" ]; then
  echo "  ✅ src/mortgage_tracker/ exists"
else
  echo "  ❌ src/mortgage_tracker/ NOT FOUND"
  exit 1
fi
echo ""

echo "================================"
echo "🚀 Running collector (real data)"
echo "================================"
echo ""

# Try python3 first, fall back to python
if command -v python3 &> /dev/null; then
  PYTHON_CMD=python3
elif command -v python &> /dev/null; then
  PYTHON_CMD=python
else
  echo "❌ No Python found"
  exit 1
fi

$PYTHON_CMD -m mortgage_tracker.main --run-type real

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Smoke test PASSED"
  exit 0
else
  echo "❌ Smoke test FAILED (exit code: $EXIT_CODE)"
  exit $EXIT_CODE
fi
