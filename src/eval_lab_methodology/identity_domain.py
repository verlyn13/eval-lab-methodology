"""Canonical identity-domain layer for score comparability.

This module is the single normative definition of the identity domain shared
by every implementation in the ecosystem: the private deployment that serves
models, the evaluation lab that runs campaigns, and this public core. Runs are
score-comparable only when their ``identity_domain_sha256`` values match
exactly, or when an explicit bridge authorization is recorded downstream in
the evidence. Anything else fails closed: a comparison that cannot prove it
crossed no identity boundary is not admitted.

An identity domain is a structural fingerprint of everything that can change
the numerics a run produces: the serving engine and its version, the serving
image and base-image digests, the engine wheel hash, the GPU hardware, the
model artifacts (repository, revision, tokenizer, chat template, and weights
fingerprint), and the launch configuration. Run-scoped identifiers -- run ids
and timestamps -- are excluded by construction, so the domain is stable across
runs on the same stack.

Reproducibility is version+hardware scoped. An engine bump or a hardware
change creates a new identity domain: that is a re-baseline, not a comparable
run.

The canonical hash of a domain is exactly::

    "sha256:" + hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
    ).hexdigest()

Hash strings match ``^sha256:[0-9a-f]{64}$``: the prefix is required and the
hex digits are lowercase. ``CONFORMANCE_IDENTITY_DOMAIN`` and its frozen hash
``CONFORMANCE_IDENTITY_DOMAIN_SHA256`` are the cross-repo conformance vector:
every downstream implementation carries a parity test that reproduces the
frozen hash from the fixture.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

IDENTITY_DOMAIN_SCHEMA_VERSION = "agentic-coding-evaluation-lab.identity-domain.v1"

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

IDENTITY_DOMAIN_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "schema_version",
    "reference_lane",
    "runtime",
    "image",
    "hardware",
    "model",
    "launch",
)

IDENTITY_DOMAIN_SECTIONS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "runtime": (
            "engine",
            "engine_version",
        ),
        "image": (
            "eval_serving_image_digest",
            "base_image_digest",
            "vllm_wheel_sha256",
        ),
        "hardware": (
            "gpu_name",
            "gpu_count",
            "vram_total_mb",
            "driver_version",
            "cuda_version",
            "compute_capability",
        ),
        "model": (
            "repo",
            "revision",
            "tokenizer_sha256",
            "chat_template_sha256",
            "weights_fingerprint_sha256",
        ),
        "launch": (
            "runner",
            "attention_backend",
            "distributed_executor_backend",
            "tensor_parallel_size",
            "pipeline_parallel_size",
            "device_ids",
            "dtype",
            "activation_dtype",
            "weight_dtype",
            "kv_cache_dtype",
            "quantization_method",
            "max_model_len",
            "trust_remote_code",
            "batch_invariant",
            "served_model_name",
        ),
    }
)

BASE_IMAGE_DIGEST_KEYS: tuple[str, ...] = (
    "version",
    "manifest_list",
    "linux_amd64",
)

FORBIDDEN_KEYS = frozenset({"run_id", "timestamp", "timestamps", "started_at", "completed_at"})


def canonical_json(payload: Any) -> str:
    """Serialize ``payload`` under the frozen canonicalization rule."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def identity_domain_sha256(domain: Mapping[str, Any]) -> str:
    """Return the prefixed canonical sha256 hash of an identity domain."""

    return "sha256:" + hashlib.sha256(canonical_json(domain).encode("utf-8")).hexdigest()


def validate_identity_domain(domain: Mapping[str, Any]) -> list[str]:
    """Fail-closed structural validation of an identity domain.

    The function returns diagnostic strings; an empty list means the domain is
    structurally valid. Only structure is checked here -- schema version,
    required sections and keys, section shapes, and the forbidden run-scoped
    keys. Value semantics belong to the downstream builders that attest them.
    """

    if not isinstance(domain, Mapping):
        return ["$ must be an object"]

    errors: list[str] = []
    for key in IDENTITY_DOMAIN_TOP_LEVEL_KEYS:
        if key not in domain:
            errors.append(f"$.{key} is required")
    if domain.get("schema_version") != IDENTITY_DOMAIN_SCHEMA_VERSION:
        errors.append(f"$.schema_version must be {IDENTITY_DOMAIN_SCHEMA_VERSION}")
    reference_lane = domain.get("reference_lane")
    if not isinstance(reference_lane, str) or not reference_lane:
        errors.append("$.reference_lane must be a non-empty string")

    for section, keys in IDENTITY_DOMAIN_SECTIONS.items():
        value = domain.get(section)
        if not isinstance(value, Mapping):
            errors.append(f"$.{section} must be an object")
            continue
        for key in keys:
            if key not in value:
                errors.append(f"$.{section}.{key} is required")

    image = domain.get("image")
    if isinstance(image, Mapping):
        base_image_digest = image.get("base_image_digest")
        if not isinstance(base_image_digest, Mapping):
            errors.append("$.image.base_image_digest must be an object")
        else:
            for key in BASE_IMAGE_DIGEST_KEYS:
                if key not in base_image_digest:
                    errors.append(f"$.image.base_image_digest.{key} is required")

    _reject_forbidden_keys(domain, "$", errors)
    return errors


def _reject_forbidden_keys(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key} must not appear in an identity domain")
            _reject_forbidden_keys(item, f"{path}.{key}", errors)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, item in enumerate(value):
            _reject_forbidden_keys(item, f"{path}[{index}]", errors)


# The cross-repo conformance vector. Every value is synthetic and public-safe;
# the digests are repeated-hex placeholders that match SHA256_PATTERN. Treat
# the fixture and its frozen hash below as immutable: downstream parity tests
# reproduce CONFORMANCE_IDENTITY_DOMAIN_SHA256 from this exact payload.
CONFORMANCE_IDENTITY_DOMAIN: dict[str, Any] = {
    "schema_version": IDENTITY_DOMAIN_SCHEMA_VERSION,
    "reference_lane": "vllm-0.25.0-dedicated",
    "runtime": {
        "engine": "vllm",
        "engine_version": "0.25.0",
    },
    "image": {
        "eval_serving_image_digest": "sha256:" + "ab" * 32,
        "base_image_digest": {
            "version": "v0.25.0",
            "manifest_list": "sha256:" + "cd" * 32,
            "linux_amd64": "sha256:" + "ef" * 32,
        },
        "vllm_wheel_sha256": "sha256:" + "12" * 32,
    },
    "hardware": {
        "gpu_name": "NVIDIA L40S",
        "gpu_count": 1,
        "vram_total_mb": 46068,
        "driver_version": "550.90.07",
        "cuda_version": "12.4",
        "compute_capability": "8.9",
    },
    "model": {
        "repo": "example-org/synthetic-model",
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "tokenizer_sha256": "sha256:" + "34" * 32,
        "chat_template_sha256": "sha256:" + "56" * 32,
        "weights_fingerprint_sha256": "sha256:" + "78" * 32,
    },
    "launch": {
        "runner": "dedicated-gpu",
        "attention_backend": "FLASH_ATTN",
        "distributed_executor_backend": "mp",
        "tensor_parallel_size": 1,
        "pipeline_parallel_size": 1,
        "device_ids": [0],
        "dtype": "bfloat16",
        "activation_dtype": "bfloat16",
        "weight_dtype": "bfloat16",
        "kv_cache_dtype": "fp8",
        "quantization_method": None,
        "max_model_len": 32768,
        "trust_remote_code": False,
        "batch_invariant": True,
        "served_model_name": "synthetic-model",
    },
}

# Frozen literal, not recomputed at import time on purpose: the constant is
# the published cross-repo conformance value, and drift must fail a test.
CONFORMANCE_IDENTITY_DOMAIN_SHA256 = (
    "sha256:174b6b7acf10e667605d2d4cf144e540ed61e020df9f2907ca089342ba72e462"
)
