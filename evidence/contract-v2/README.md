# Contract B v2 synthetic fixture

`synthetic-not-evaluable.json` is a public-safe structural fixture for the
immutable `2.0.0-draft.1` schema. It contains no real task, model, response,
grader, provider, host, endpoint, credential, or deployment fact. It selects no
inferential method and can only recompute to `NOT_EVALUABLE`.
`synthetic-not-evaluable-report.md` is the byte-checked human-readable rendering
of the independently recomputed report model.

The registration copy follows the immutable public
`eval-registry.registration-receipt.v1` shape and domains. Its digest covers the
exact embedded `receipt.json` UTF-8 bytes, not a reconstructed serialization.
The copied `eval-registry.verification-result.v1` is informational and refuses
under the registry's D2 posture: it claims no operational signer identity,
issuer, trust policy, signature, timestamp, or registration adapter.

The observation join separates pre-launch editing-harness-owner descriptor
validation from post-run evaluation-harness process completion. Gateway
ownership is also explicit: every invocation has distinct owner open and close
receipts; zero or more call receipts sit between them; the close receipt binds
the open digest, call count, ordered request-ID digest, and a domain-separated
digest of each ordered request-ID/owner-receipt pair. Zero calls use the
canonical empty-list binding and are valid only for a retained pre-dispatch
failure. Any fallback is forbidden. Actual request-attempt counts and vectors
remain gateway-owned, never editing-harness facts.

The editing-harness, evaluation-harness, and gateway owner receipt schemas and
provenance classes in this fixture are versioned synthetic placeholders marked
`synthetic-fixture-unratified`. They demonstrate copy-preserving joins but are
not operational mappings; later integration must consume the owners' frozen
receipt classes without upgrading provenance. Operational adoption must
validate each exact owner receipt against its frozen owner schema; copied source
envelopes are evidence pointers, never verification inputs.

The verifier implementation is repository-only under `analysis/contract_v2/`.
The fixture binds the exact schema bytes and separately binds an ordered
path-and-byte-digest manifest plus aggregate digest for the verifier, human
report renderer, and publication-safety scanner. None is part of the
wheel-buildable repository package version 0.2.0.

The single exact-byte verification entry point requires `jsonschema` and
validates this fixture with Draft 2020-12 before independent recomputation. The
CLI, Quarto page, and acceptance tests all use that path. A missing validator or
schema violation is a normalized verification refusal, never a skipped test.

## Frozen repository delivery surface

`delivery-manifest.v1.json` is the immutable, canonical-JSON delivery contract
for copying this repository-only draft into a private evaluation deployment. It
pins the public source commit and tree, the unchanged repository core identity
at version 0.2.0, the
exact schema/verifier/report/publication-safety bytes, their required relative
layout, the `jsonschema` runtime requirement, and the synthetic conformance
fixture and golden report. The runtime-file aggregate is computed over the
ordered canonical list of `{path, sha256}` records; a downstream lock also pins
the exact manifest bytes and the exact resolved validator dependency version.

The public Git commit is published and reviewable. The Contract B implementation
remains an unreleased, repository-only normative draft with no operational
authority and is not part of the 0.2.0 wheel. A consumer must verify every file
before import, preserve the listed paths because schema discovery is relative to
the verifier, and refuse on any missing, changed, duplicate, or unexpected
entry. The import surface is `analysis.contract_v2:verify_exact_bytes`; Markdown
rendering is `analysis.contract_v2.report:render_markdown`. The existing
`python -m analysis.run_contract_v2 --check` command remains the repository
conformance command and is not required in the minimal runtime mirror.

The published `2.0.0-draft.1` contract, schema, verifier, report renderer, and
publication-safety bytes are never edited in place. A change to any of those
bytes requires a new reviewed Contract B version. A transport-only change to a
future delivery manifest requires a new delivery revision and downstream review.

## Sanitization-hardening provenance

The durable, public provenance for the independent recursive content scan is
fully in-repository: `scripts/publication_safety.py` contains the shared scanner,
`scripts/render_methodology_report.py` and the v2 verifier invoke it, and the
report-layer and Contract B tests exercise its refusal behavior. Its cleartext
generic patterns, hash-only private-name denylist, and refusal semantics can
therefore be reviewed from reachable repository bytes without relying on a
history object outside the published branch.

Integration order is explicit: land the independent scanner first or in the
same reviewed change, then permit the v2 report fixture to render. Producer
sanitization flags are never treated as proof.
