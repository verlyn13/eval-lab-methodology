EVIDENCE ?= evidence/sample-lab-report.json
REPORT ?= reports/methodology-report.qmd
OUTPUT_DIR ?= reports/rendered

.PHONY: render validate-report validate-contract-v2

render:
	python scripts/render_methodology_report.py --evidence "$(EVIDENCE)" --report "$(REPORT)" --output-dir "$(OUTPUT_DIR)"

validate-report:
	python scripts/render_methodology_report.py --evidence "$(EVIDENCE)" --validate-only

validate-contract-v2:
	PYTHONPATH=src python -m analysis.run_contract_v2 --check
