from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pkgutil
import yaml


@dataclass(frozen=True)
class RamAddress:
    domain: str
    address: int
    size: int = 1
    max_value: int = 0xFF


@dataclass(frozen=True)
class KirbyAMRamSpec:
    # Guards used by BizHawk read/write calls to ensure game is “in a safe state”.
    guards: dict[str, Any]

    # POC signals
    room_id: RamAddress
    max_hp: RamAddress

    # Optional filler signal
    phone_charge: Optional[RamAddress]


def _require_int(v: Any, field: str) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        # allow hex strings like "0x1234"
        return int(v, 0)
    raise ValueError(f"{field} must be int or int-like string, got {type(v).__name__}")


def _load_yaml_bytes() -> bytes:
    data = pkgutil.get_data(__name__.rsplit(".", 1)[0], "data/ram.yaml")
    if data is None:
        raise FileNotFoundError("Missing worlds/kirbyam/data/ram.yaml")
    return data


def load_ram_spec() -> KirbyAMRamSpec:
    raw = yaml.safe_load(_load_yaml_bytes())
    if not isinstance(raw, dict):
        raise ValueError("ram.yaml must be a mapping")

    guards = raw.get("guards", {})
    if not isinstance(guards, dict):
        raise ValueError("ram.yaml guards must be a mapping")

    def parse_addr(key: str, *, required: bool = True) -> Optional[RamAddress]:
        node = raw.get(key)
        if node is None:
            if required:
                raise ValueError(f"ram.yaml missing required key: {key}")
            return None
        if not isinstance(node, dict):
            raise ValueError(f"ram.yaml {key} must be a mapping")

        domain = str(node.get("domain", "System Bus"))
        address = _require_int(node.get("address"), f"{key}.address")
        size = int(node.get("size", 1))
        max_value = int(node.get("max_value", 0xFF))
        return RamAddress(domain=domain, address=address, size=size, max_value=max_value)

    return KirbyAMRamSpec(
        guards=guards,
        room_id=parse_addr("room_id", required=True),
        max_hp=parse_addr("max_hp", required=True),
        phone_charge=parse_addr("phone_charge", required=False),
    )
