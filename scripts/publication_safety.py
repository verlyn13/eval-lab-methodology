"""Independent recursive public-boundary scan shared by report validators.

The durable provenance for this shared scanner is the source and refusal tests
committed in this repository. Producer ``public-safe`` booleans remain
necessary but are never proof.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

PRIVATE_NAME_SHA256_DENYLIST = frozenset(
    {
        "sha256:31d1b3d540ecf85228db7797efbe7d198ec5406abd3f6e64f27f684e9a312d29",
        "sha256:5297625bd75d4fd27c2bb02e1a78f8c125182f2c540c7e5739057ae0662b6dd4",
        "sha256:853d7344bbd8fdc02f62d505025362e5b3ee17bd3a3980af4ba07d5c0b2ae36e",
        "sha256:8d17ba3f0fcdcea0150410539b1318022c25dd52b46b1e9e306246865c6f8c57",
        "sha256:99860b65912fb343c665ab6457d1b2fb4bf87fb46b4b8e53a96aa408010ab9f5",
        "sha256:a956b2f69f60121451fb578b4bfcac9017d421cf01aebf7b56105a45690d2e3c",
        "sha256:e9874dcc220dc76251458f3e9c6875f826055b2cfee6ac5b42fd0dfeb1a6c9f3",
        "sha256:ebde709e306badca2f843f1ef91c7fb216a99aa4417b32fe911e15acfff8bedd",
    }
)

_GENERIC_LEAK_PATTERNS = (
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(?:api[ _-]?key|access[ _-]?token|authorization|bearer|password|"
            r"secret(?:[ _-]?(?:file|path))?)\b\s*(?:=|:)\s*[^\s,;]{6,}"
        ),
    ),
    ("secret-manager URI", re.compile(r"(?i)\b(?:op|vault)://[^\s]+")),
    (
        "credential-bearing network endpoint",
        re.compile(r"(?i)\b(?:https?|wss?)://[^\s/@:]+:[^\s/@]+@[^\s]+"),
    ),
    ("object-store URI", re.compile(r"(?i)\bs3://[^\s]+")),
    (
        "internal hostname",
        re.compile(
            r"(?i)\b[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.(?:corp|internal|lan|local)\b"
        ),
    ),
    (
        "absolute workstation path",
        re.compile(r"(?:^|[\s\"'])(?:/Users/|/home/|~/)[^\s\"']*"),
    ),
    (
        "cloud resource identifier",
        re.compile(
            r"(?i)\b(?:account|billing|bucket|object|pod|project|tenant|workspace)"
            r"[ _-]?id\b\s*(?:=|:)\s*[a-z0-9][a-z0-9._:/-]{5,}"
        ),
    ),
)

_IPV4_CANDIDATE = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
_NAME_TOKENS = re.compile(r"[^\W_]+", re.UNICODE)
_MAX_PRIVATE_NAME_TOKENS = 8
_MAX_REPORTED_SCAN_FAILURES = 12


def normalized_name_sha256(value: str) -> str:
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKC", value).casefold()
        if character.isalnum()
    )
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _walk_scalar_text(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, Mapping):
        for index, (key, child) in enumerate(value.items()):
            yield f"{path}.key[{index}]", str(key)
            if not isinstance(child, Mapping | Sequence) or isinstance(
                child, str | bytes | bytearray
            ):
                yield f"{path}.pair[{index}]", f"{key}:{child}"
            yield from _walk_scalar_text(child, f"{path}.value[{index}]")
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, child in enumerate(value):
            yield from _walk_scalar_text(child, f"{path}[{index}]")
        return
    yield path, str(value)


def _contains_ipv4_address(value: str) -> bool:
    for match in _IPV4_CANDIDATE.finditer(value):
        octets = match.group(0).split(".")
        if all(int(octet) <= 255 for octet in octets):
            return True
    return False


def _contains_denylisted_name(value: str, denylist: frozenset[str]) -> bool:
    folded = unicodedata.normalize("NFKC", value).casefold()
    tokens = _NAME_TOKENS.findall(folded)
    for start in range(len(tokens)):
        for width in range(1, min(_MAX_PRIVATE_NAME_TOKENS, len(tokens) - start) + 1):
            candidate = "".join(tokens[start : start + width])
            if len(candidate) >= 4 and normalized_name_sha256(candidate) in denylist:
                return True
    return False


def assert_publication_content_is_safe(
    document: Any,
    *,
    private_name_sha256s: frozenset[str] = PRIVATE_NAME_SHA256_DENYLIST,
) -> None:
    """Refuse content leaks independently of producer assertions."""

    failures: list[str] = []
    for location, value in _walk_scalar_text(document):
        for rule, pattern in _GENERIC_LEAK_PATTERNS:
            if pattern.search(value):
                failures.append(f"{location}: {rule}")
        if _contains_ipv4_address(value):
            failures.append(f"{location}: IP address")
        if _contains_denylisted_name(value, private_name_sha256s):
            failures.append(f"{location}: hashed private-identifier denylist")
    if failures:
        unique = list(dict.fromkeys(failures))
        shown = unique[:_MAX_REPORTED_SCAN_FAILURES]
        omitted = len(unique) - len(shown)
        suffix = f"; {omitted} additional finding(s) omitted" if omitted else ""
        raise ValueError(
            "independent recursive content scan found " + "; ".join(shown) + suffix
        )
