#!/usr/bin/env bash
# Generate a throwaway RSA keypair for local dry-runs (NOT for production GitHub Apps).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/private-key.pem}"
openssl genrsa -out "$OUT" 2048
chmod 600 "$OUT"
echo "Wrote $OUT"
echo "Remember: production keys must be downloaded from GitHub App settings."
