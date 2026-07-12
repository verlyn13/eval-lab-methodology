from __future__ import annotations

import copy
import json
import unittest

from eval_lab_methodology import (
    CONFORMANCE_IDENTITY_DOMAIN,
    CONFORMANCE_IDENTITY_DOMAIN_SHA256,
    IDENTITY_DOMAIN_SCHEMA_VERSION,
    SHA256_PATTERN,
    canonical_json,
    identity_domain_sha256,
    validate_identity_domain,
)


def _reordered(value):
    if isinstance(value, dict):
        return {key: _reordered(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [_reordered(item) for item in value]
    return value


class IdentityDomainHashTests(unittest.TestCase):
    def test_frozen_conformance_vector_reproduces(self) -> None:
        self.assertEqual(
            identity_domain_sha256(CONFORMANCE_IDENTITY_DOMAIN),
            CONFORMANCE_IDENTITY_DOMAIN_SHA256,
        )
        self.assertRegex(CONFORMANCE_IDENTITY_DOMAIN_SHA256, SHA256_PATTERN)

    def test_hash_is_key_order_independent(self) -> None:
        reordered = _reordered(copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN))
        self.assertNotEqual(list(reordered), list(CONFORMANCE_IDENTITY_DOMAIN))
        self.assertEqual(
            identity_domain_sha256(reordered),
            CONFORMANCE_IDENTITY_DOMAIN_SHA256,
        )

    def test_canonical_json_uses_compact_separators_and_ascii_escapes(self) -> None:
        self.assertEqual(
            canonical_json({"b": [1, 2], "a": "café"}),
            '{"a":"caf\\u00e9","b":[1,2]}',
        )

    def test_non_ascii_changes_bytes_deterministically(self) -> None:
        accented = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        accented["reference_lane"] = "vllm-0.25.0-dédicated"
        self.assertIn("\\u00e9", canonical_json(accented))
        self.assertNotEqual(
            identity_domain_sha256(accented),
            CONFORMANCE_IDENTITY_DOMAIN_SHA256,
        )
        self.assertEqual(identity_domain_sha256(accented), identity_domain_sha256(accented))

    def test_pattern_requires_prefixed_lowercase_64_hex(self) -> None:
        digest = "0" * 64
        self.assertIsNotNone(SHA256_PATTERN.fullmatch(f"sha256:{digest}"))
        self.assertIsNone(SHA256_PATTERN.fullmatch(digest))
        self.assertIsNone(SHA256_PATTERN.fullmatch(f"sha256:{'A' * 64}"))
        self.assertIsNone(SHA256_PATTERN.fullmatch(f"sha256:{'0' * 63}"))
        self.assertIsNone(SHA256_PATTERN.fullmatch(f"sha256:{'0' * 65}"))


class IdentityDomainValidationTests(unittest.TestCase):
    def test_conformance_vector_is_structurally_valid(self) -> None:
        self.assertEqual(validate_identity_domain(CONFORMANCE_IDENTITY_DOMAIN), [])

    def test_rejects_missing_section(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid.pop("hardware")
        errors = validate_identity_domain(invalid)
        self.assertIn("$.hardware is required", errors)
        self.assertIn("$.hardware must be an object", errors)

    def test_rejects_missing_launch_key(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid["launch"].pop("batch_invariant")
        self.assertIn("$.launch.batch_invariant is required", validate_identity_domain(invalid))

    def test_rejects_run_id_at_top_level(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid["run_id"] = "2026-07-12T000000Z_synthetic"
        self.assertIn(
            "$.run_id must not appear in an identity domain",
            validate_identity_domain(invalid),
        )

    def test_rejects_run_id_nested_inside_launch(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid["launch"]["run_id"] = "2026-07-12T000000Z_synthetic"
        self.assertIn(
            "$.launch.run_id must not appear in an identity domain",
            validate_identity_domain(invalid),
        )

    def test_rejects_wrong_schema_version(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid["schema_version"] = "some-other-domain.v1"
        self.assertIn(
            f"$.schema_version must be {IDENTITY_DOMAIN_SCHEMA_VERSION}",
            validate_identity_domain(invalid),
        )

    def test_rejects_non_mapping_section(self) -> None:
        invalid = copy.deepcopy(CONFORMANCE_IDENTITY_DOMAIN)
        invalid["runtime"] = ["vllm", "0.25.0"]
        self.assertIn("$.runtime must be an object", validate_identity_domain(invalid))

    def test_conformance_vector_is_json_serializable_and_synthetic(self) -> None:
        payload = json.loads(canonical_json(CONFORMANCE_IDENTITY_DOMAIN))
        self.assertEqual(payload["schema_version"], IDENTITY_DOMAIN_SCHEMA_VERSION)
        self.assertEqual(payload["model"]["repo"], "example-org/synthetic-model")
        self.assertEqual(payload["launch"]["activation_dtype"], payload["launch"]["dtype"])


if __name__ == "__main__":
    unittest.main()
