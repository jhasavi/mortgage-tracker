#!/usr/bin/env bash
set -euo pipefail

# Map secret name (used in GitHub) -> name expected by scripts/python
export SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-${SUPABASE_SERVICE_ROLE:-}}"

if [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "❌ Missing SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SERVICE_ROLE)."
  exit 1
fi

bash scripts/mvp_smoke_test.sh
bash scripts/verify_deployment.sh
