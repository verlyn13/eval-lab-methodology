#!/usr/bin/env bash
set -euo pipefail

required_quarto_version="$(tr -d '[:space:]' < .quarto-version)"
if ! command -v quarto >/dev/null 2>&1; then
  echo "Quarto ${required_quarto_version} is required; see README.md" >&2
  exit 1
fi
actual_quarto_version="$(quarto --version)"
if [[ "${actual_quarto_version}" != "${required_quarto_version}" ]]; then
  echo "Quarto ${required_quarto_version} is required; found ${actual_quarto_version}" >&2
  exit 1
fi

wheel_dir="$(mktemp -d)"
trap 'rm -rf -- "${wheel_dir}"' EXIT

ruff check .
ruff format --check .
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m analysis.run_method_tranche --check
PYTHONPATH=src python -m analysis.run_contract_v2 --check
PYTHONPATH=src python -m analysis.run_calibration_freeze --check
python -m pip wheel . --no-deps -w "${wheel_dir}"
make validate-report EVIDENCE=evidence/sample-lab-report.json
quarto render
python scripts/render_methodology_report.py \
  --evidence evidence/sample-lab-report.json \
  --report reports/methodology-report.qmd \
  --output-dir reports/rendered/sample

html_path="$(find reports/rendered/sample -name 'methodology-report.html' -print -quit)"
if [[ -z "${html_path}" ]]; then
  echo "rendered sample report not found under reports/rendered/sample" >&2
  exit 1
fi
if [[ "${html_path}" != "reports/rendered/sample/methodology-report.html" ]]; then
  mv "${html_path}" reports/rendered/sample/methodology-report.html
fi

shopt -s nullglob globstar
campaign_files=(evidence/campaigns/**/evidence.json)
for evidence in "${campaign_files[@]}"; do
  safe_name="${evidence#evidence/campaigns/}"
  safe_name="${safe_name%/evidence.json}"
  safe_name="${safe_name//\//-}"
  output_dir="reports/rendered/campaigns/${safe_name}"
  make validate-report EVIDENCE="${evidence}"
  python scripts/render_methodology_report.py \
    --evidence "${evidence}" \
    --report reports/methodology-report.qmd \
    --output-dir "${output_dir}"
done
