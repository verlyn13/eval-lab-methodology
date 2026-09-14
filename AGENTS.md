# Public methodology agent contract

## Purpose and public boundary

This public repository owns the infrastructure-independent statistical and reporting core, the normative identity-domain specification and conformance vectors, the public evidence contract, reproducible figures, and Quarto reports. Every committed byte is world-readable, and merging to `main` publishes the site.

The repository does not own private evaluation fixtures, runtime plumbing, model routing, credentials, deployment state, or raw campaign artifacts. Describe private integrations only by function. Never include a private repository name, workspace path, host, endpoint, account identifier, or secret reference.

## Start every task

1. Use the `project-status` skill.
2. Read `STATUS.md`, `README.md`, `PLAN.md`, `ERRATA.md`, and the relevant evidence contract or report source.
3. Inspect the current branch, HEAD, working tree, and relevant diff. Preserve unrelated work.
4. Keep checked-in public source, local Git, rendered output, publication state, and private producer claims as separate evidence lanes. A producer label is not independent sanitization proof.

## Durable rules

- Run the public-boundary and evidence validators before rendering or committing. Publish only synthetic or independently sanitized data.
- Every published number must trace to a validated artifact. Label enforcing, advisory, planned, and not-evaluable outcomes accurately.
- Treat exact evidence bytes as the verification input. Do not replace exact-byte checks with reconstructed semantic equivalence.
- The published identity-domain version and conformance vector are immutable. A semantic change creates a new schema version and vector alongside the old version.
- Never commit raw prompts, responses, task fixtures, provider captures, infrastructure identifiers, credentials, or unverified values.
- Real-run evidence or figures require a complete sanitization review and the repository's human publication gate.

## Engineering policy

Prefer forward migrations. Upgrade Python, Quarto, rendering libraries, and schema tooling by updating the declared baseline, rebuilding artifacts, and running the full public gate. Do not downgrade a workstation to preserve an obsolete renderer. Preserve published contracts through explicit versioning, not by freezing the surrounding toolchain.

Keep current release state and dated findings in `STATUS.md`, `PLAN.md`, and Git. Project agents inherit the user-selected model.

## Validation and handoff

Install the locked development/report extras, then run:

```bash
uv sync --frozen --no-install-project --extra dev --extra report
python3 scripts/check_agent_contract.py
uv run --frozen --no-sync bash scripts/run-merge-gate.sh
```

The merge-gate script owns local/CI parity, including the declared Quarto version, lint, tests, exact-result checks, wheel containment, evidence validation, site rendering, and report rendering. Update `STATUS.md`, `README.md`, or `PLAN.md` when their owned truth changes. Treat a merge as a publication action.
