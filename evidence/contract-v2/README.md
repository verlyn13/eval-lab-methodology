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
report renderer, and publication-safety scanner. None is part of the released
0.2.0 wheel.

The single exact-byte verification entry point requires `jsonschema` and
validates this fixture with Draft 2020-12 before independent recomputation. The
CLI, Quarto page, and acceptance tests all use that path. A missing validator or
schema violation is a normalized verification refusal, never a skipped test.

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
