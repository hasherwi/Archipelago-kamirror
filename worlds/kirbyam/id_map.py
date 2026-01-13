from __future__ import annotations

import hashlib
from typing import Dict, Iterable, Tuple, Mapping

# Keep these offsets stable forever once published.
ITEM_ID_BASE = 1000
LOCATION_ID_BASE = 10000

def _stable_hash32(text: str) -> int:
    # Deterministic across runs and machines (unlike Python's built-in hash()).
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


def build_id_map(keys: Iterable[str], base_id: int, namespace: str) -> Dict[str, int]:
    """
    Allocate deterministic numeric IDs for a set of keys.

    - Uses a stable hash of (namespace + ":" + key)
    - Produces values in a wide range above base_id
    - Detects collisions and raises if they occur

    You MUST keep base_id stable once published.
    
    IDs are derived from canonical YAML keys (not names).
    Keys must remain stable once published.
    
    """
    mapping: Dict[str, int] = {}
    used: Dict[int, str] = {}

    for key in sorted(keys):
        h = _stable_hash32(f"{namespace}:{key}")
        # Spread IDs in a large space while keeping them positive.
        assigned = base_id + (h % 1_000_000_000)

        if assigned in used and used[assigned] != key:
            other = used[assigned]
            raise ValueError(
                f"ID collision for namespace '{namespace}': '{key}' and '{other}' -> {assigned}. "
                f"Change base_id or adjust key(s)."
            )

        used[assigned] = key
        mapping[key] = assigned

    return mapping

def build_id_map_from_keys(keys: Iterable[str], base: int) -> dict[str, int]:
    """
    Deterministically assign numeric IDs from a sorted list of canonical keys.
    Canonical identifier is the YAML 'key' field.
    """
    sorted_keys = sorted(keys)
    return {k: base + i for i, k in enumerate(sorted_keys)}


def build_item_key_to_id(items: Iterable[Mapping[str, object]]) -> dict[str, int]:
    keys = [str(row["key"]) for row in items]
    return build_id_map_from_keys(keys, ITEM_ID_BASE)


def build_location_key_to_id(locations: Iterable[Mapping[str, object]]) -> dict[str, int]:
    keys = [str(row["key"]) for row in locations]
    return build_id_map_from_keys(keys, LOCATION_ID_BASE)
