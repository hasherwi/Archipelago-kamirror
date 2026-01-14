from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple

from worlds._bizhawk.client import BizHawkClient
from worlds._bizhawk.context import BizHawkClientContext

from .ram import KirbyAMRamSpec, load_ram_spec

GAME_NAME = "Kirby & The Amazing Mirror"

logger = logging.getLogger(__name__)

# slot_data["poc"] keys (adjust here if your slot_data structure differs)
POC_ROOT_KEY = "poc"
POC_LOCATIONS_KEY = "locations"
POC_ITEMS_KEY = "items"

POC_ROOM_CHECK_KEY = "room_check"
POC_GOAL_KEY = "goal"

POC_ITEM_MAX_HEALTH_KEY = "max_health_up"
POC_ITEM_PHONE_CHARGE_KEY = "phone_charge"


@dataclass(frozen=True)
class _LocationTrigger:
    loc_id: int
    room_value_na: int


@dataclass(frozen=True)
class _POCConfig:
    room_check: _LocationTrigger
    goal: _LocationTrigger

    max_health_item_id: int
    phone_charge_item_id: int


def _expect_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Expected int at {path}, got {type(value).__name__}: {value!r}")
    return value


def _get_poc_slot(ctx: BizHawkClientContext) -> Dict[str, Any]:
    if not isinstance(getattr(ctx, "slot_data", None), dict):
        raise ValueError("ctx.slot_data is not available or not a dict yet")
    root = ctx.slot_data.get(POC_ROOT_KEY)
    if not isinstance(root, dict):
        raise ValueError(f"slot_data[{POC_ROOT_KEY!r}] is missing or not a dict")
    return root


def _parse_trigger(poc: Dict[str, Any], trigger_key: str) -> _LocationTrigger:
    locs = poc.get(POC_LOCATIONS_KEY)
    if not isinstance(locs, dict):
        raise ValueError(f"slot_data['{POC_ROOT_KEY}']['{POC_LOCATIONS_KEY}'] missing or not a dict")

    raw = locs.get(trigger_key)
    if not isinstance(raw, dict):
        raise ValueError(
            f"slot_data['{POC_ROOT_KEY}']['{POC_LOCATIONS_KEY}']['{trigger_key}'] missing or not a dict"
        )

    loc_id = _expect_int(raw.get("id"), f"{POC_ROOT_KEY}.{POC_LOCATIONS_KEY}.{trigger_key}.id")
    room_value = _expect_int(
        raw.get("room_value_na"), f"{POC_ROOT_KEY}.{POC_LOCATIONS_KEY}.{trigger_key}.room_value_na"
    )
    return _LocationTrigger(loc_id=loc_id, room_value_na=room_value)


def _parse_item_id(poc: Dict[str, Any], item_key: str) -> int:
    items = poc.get(POC_ITEMS_KEY)
    if not isinstance(items, dict):
        raise ValueError(f"slot_data['{POC_ROOT_KEY}']['{POC_ITEMS_KEY}'] missing or not a dict")

    raw = items.get(item_key)
    if not isinstance(raw, dict):
        raise ValueError(f"slot_data['{POC_ROOT_KEY}']['{POC_ITEMS_KEY}']['{item_key}'] missing or not a dict")

    return _expect_int(raw.get("id"), f"{POC_ROOT_KEY}.{POC_ITEMS_KEY}.{item_key}.id")


class KirbyAMBizHawkClient(BizHawkClient):
    game = GAME_NAME

    def __init__(self) -> None:
        super().__init__()
        self._ram: Optional[KirbyAMRamSpec] = None
        self._poc: Optional[_POCConfig] = None

        # POC runtime state
        self._checked_locations: Set[int] = set()
        self._last_room_value: Optional[int] = None

        # Item application cursor
        self._items_applied: int = 0

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        # Optional: if you later add ROM signature validation in ram.yaml, implement it here.
        return True

    def _ensure_ram_loaded(self) -> KirbyAMRamSpec:
        if self._ram is None:
            self._ram = load_ram_spec()
            logger.info("Loaded ram spec")
        return self._ram

    def _ensure_poc_loaded(self, ctx: BizHawkClientContext) -> _POCConfig:
        if self._poc is not None:
            return self._poc

        poc = _get_poc_slot(ctx)

        room_check = _parse_trigger(poc, POC_ROOM_CHECK_KEY)
        goal = _parse_trigger(poc, POC_GOAL_KEY)

        max_health_item_id = _parse_item_id(poc, POC_ITEM_MAX_HEALTH_KEY)
        phone_charge_item_id = _parse_item_id(poc, POC_ITEM_PHONE_CHARGE_KEY)

        self._poc = _POCConfig(
            room_check=room_check,
            goal=goal,
            max_health_item_id=max_health_item_id,
            phone_charge_item_id=phone_charge_item_id,
        )

        logger.info(
            "Loaded POC slot_data: room_check(loc_id=%s room_value_na=%s) goal(loc_id=%s room_value_na=%s) "
            "items(max_health=%s phone_charge=%s)",
            room_check.loc_id,
            room_check.room_value_na,
            goal.loc_id,
            goal.room_value_na,
            max_health_item_id,
            phone_charge_item_id,
        )
        return self._poc

    def _read_room_value_na(self, ctx: BizHawkClientContext, ram: KirbyAMRamSpec) -> int:
        """
        Reads the current room value from RAM.

        This assumes your BizHawkClientContext provides read_u8 / read_u16_le.
        If your environment instead requires ctx.bizhawk_ctx.read(...) or similar,
        change this function only; the rest of the client remains stable.
        """
        region = ram.na

        if region.room_id_width == 1:
            return int(ctx.read_u8(region.room_id_addr))

        # default: u16 little-endian
        return int(ctx.read_u16_le(region.room_id_addr))

    async def _send_location_check(self, ctx: BizHawkClientContext, loc_id: int) -> None:
        if loc_id in self._checked_locations:
            return
        self._checked_locations.add(loc_id)

        await ctx.send_msgs(
            [
                {
                    "cmd": "LocationChecks",
                    "locations": [loc_id],
                }
            ]
        )

    async def _apply_received_items(self, ctx: BizHawkClientContext, poc: _POCConfig, ram: KirbyAMRamSpec) -> None:
        items_received = getattr(ctx, "items_received", None)
        if not isinstance(items_received, list) or not items_received:
            return

        if self._items_applied >= len(items_received):
            return

        new_items = items_received[self._items_applied :]
        self._items_applied = len(items_received)

        for net_item in new_items:
            item_id = getattr(net_item, "item", None)
            if not isinstance(item_id, int):
                continue

            if item_id == poc.max_health_item_id:
                await self._give_max_health(ctx, ram)
            elif item_id == poc.phone_charge_item_id:
                await self._give_phone_charge(ctx, ram)
            else:
                # Unknown / unimplemented item: ignore safely.
                pass

    async def _give_max_health(self, ctx: BizHawkClientContext, ram: KirbyAMRamSpec) -> None:
        """
        Minimal implementation: increment max HP by 1 up to max_value.
        Assumes ctx has async read/write helpers on BizHawkClient, or that your
        BizHawkClientContext exposes equivalent APIs.

        If your current stack doesn't support these exact read/write calls yet,
        keep this as a no-op until your memory bridge is finalized.
        """
        spec = ram.max_hp
        if spec is None:
            return

        # If your BizHawk layer is different, change these two calls only.
        cur = await ctx.read_int(spec.domain, spec.address, spec.size, signed=False, little_endian=True)
        new = min(cur + 1, spec.max_value)
        await ctx.write_int(spec.domain, spec.address, new, spec.size, signed=False, little_endian=True)

        logger.info("Applied Max Health Up: %s -> %s", cur, new)

    async def _give_phone_charge(self, ctx: BizHawkClientContext, ram: KirbyAMRamSpec) -> None:
        """
        Optional: increment a phone charge counter, if present in ram.yaml.
        """
        spec = ram.phone_charge
        if spec is None:
            return

        cur = await ctx.read_int(spec.domain, spec.address, spec.size, signed=False, little_endian=True)
        new = min(cur + 1, spec.max_value)
        await ctx.write_int(spec.domain, spec.address, new, spec.size, signed=False, little_endian=True)

        logger.info("Applied Phone Charge: %s -> %s", cur, new)

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        """
        Called every client tick.

        Responsibilities:
        - Load ram.yaml + slot_data POC config once available
        - Read current room value
        - Fire LocationChecks when room matches triggers
        - Apply received items
        """
        # Slot data is not always available immediately after connect.
        if not isinstance(getattr(ctx, "slot_data", None), dict):
            return

        ram = self._ensure_ram_loaded()
        poc = self._ensure_poc_loaded(ctx)

        room_value = self._read_room_value_na(ctx, ram)

        # Reduce log spam: only log on room change
        if room_value != self._last_room_value:
            logger.debug("Room changed: %s -> %s", self._last_room_value, room_value)
            self._last_room_value = room_value

        # Trigger: room check
        if room_value == poc.room_check.room_value_na:
            await self._send_location_check(ctx, poc.room_check.loc_id)

        # Trigger: goal
        if room_value == poc.goal.room_value_na:
            await self._send_location_check(ctx, poc.goal.loc_id)

        # Apply item effects after location triggers
        await self._apply_received_items(ctx, poc, ram)
