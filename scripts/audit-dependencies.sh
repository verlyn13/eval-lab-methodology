#!/usr/bin/env bash
set -euo pipefail

readonly pip_audit_version="2.10.1"
requirements_file="$(mktemp "${TMPDIR:-/tmp}/eval-lab-methodology-requirements.XXXXXX.txt")"
trap 'rm -f "${requirements_file}"' EXIT

uv export \
  --frozen \
  --all-extras \
  --no-emit-project \
  --format requirements-txt \
  --output-file "${requirements_file}" \
  --quiet
uvx --from "pip-audit==${pip_audit_version}" \
  pip-audit --disable-pip -r "${requirements_file}"
