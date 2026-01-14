from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml


@dataclass(frozen=True)
class KirbyAMRAMRegion:
    room_id_addr: int
    max_hp_addr: int
    cur_hp_addr: Optional[int]
    phone_charge_addr: int
    phone_charge_cap: int
    # width is bytes: 1 or 2 are the common cases for GBA values (u8/u16 LE)
    room_id_width: int = 2
    hp_width: int = 1
    phone_width: int = 1


@dataclass(frozen=True)
class KirbyAMRAMConfig:
    schema_version: int
    na: KirbyAMRAMRegion


def _require_int(m: Mapping[str, Any], key: str) -> int:
    v = m.get(key)
    if not isinstance(v, int):
        raise ValueError(f"ram.yaml: expected int for '{key}', got {v!r}")
    return v


def _optional_int(m: Mapping[str, Any], key: str) -> Optional[int]:
    v = m.get(key)
    if v is None:
        return None
    if not isinstance(v, int):
        raise ValueError(f"ram.yaml: expected int or null for '{key}', got {v!r}")
    return v


def load_ram_config(path: Path) -> KirbyAMRAMConfig:
    """
    Minimal, safe loader for ram.yaml (client-side).
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("ram.yaml: expected mapping at top level")

    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise ValueError(f"ram.yaml: unsupported schema_version={schema_version!r} (expected 1)")

    na_raw = raw.get("na")
    if not isinstance(na_raw, dict):
        raise ValueError("ram.yaml: missing 'na' mapping")

    na = KirbyAMRAMRegion(
        room_id_addr=_require_int(na_raw, "room_id_addr"),
        max_hp_addr=_require_int(na_raw, "max_hp_addr"),
        cur_hp_addr=_optional_int(na_raw, "cur_hp_addr"),
        phone_charge_addr=_require_int(na_raw, "phone_charge_addr"),
        phone_charge_cap=_require_int(na_raw, "phone_charge_cap"),
        room_id_width=int(na_raw.get("room_id_width", 2)),
        hp_width=int(na_raw.get("hp_width", 1)),
        phone_width=int(na_raw.get("phone_width", 1)),
    )
    return KirbyAMRAMConfig(schema_version=1, na=na)
