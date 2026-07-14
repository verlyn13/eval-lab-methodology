# Versioned interpretation errata

## Identity-domain v1

- Erratum: `identity-domain-v1-interpretation-001`
- Status: active
- Date: 2026-07-14
- Applies to repository package version `0.2.0`

The module docstring in `src/eval_lab_methodology/identity_domain.py` says that a matching v1 hash
establishes score comparability and describes the hash as covering everything that can change
numerics. That interpretation is too broad.

Identity-domain v1 hashes only its enumerated declared fields. Equality is a necessary admission
check; it does not prove numerical equivalence. Prefix-cache state, batch context, session position,
decoding parameters, harness version, and other unrecorded serving state can differ while the hash
matches. A bridge records an operator-attested exception and does not prove equivalence.

This erratum supersedes the module docstring's interpretation only. It does not modify the frozen v1
field set, canonicalization algorithm, conformance vector, package bytes, or downstream parity
requirements. Correcting the module text itself requires a new reviewed repository package version.
