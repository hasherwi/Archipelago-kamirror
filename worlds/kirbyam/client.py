from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from NetUtils import ClientStatus
from worlds._bizhawk.client import BizHawkClient
from worlds._bizhawk.context import BizHawkClientContext
from worlds._bizhawk import memory

from .ram import KirbyAMRamSpec, load_ram_spec

GAME_NAME = "Kirby & The Amazing Mirror"


@dataclass(frozen=True)
class _POCConfig:
    # These names must match your YAML names used by the world.
    room_check_location_name: str
    victory_location_name: str

    # Room ids for triggers (from ram.yaml)
    room_check_room_id: int
    goal_room_id: int

    # Item names must match your items.yaml
    max_health_item_name: str
    phone_charge_item_name: str


class KirbyAMBizHawkClient(BizHawkClient):
    game = GAME_NAME

    def __init__(self) -> None:
        super().__init__()
        self._ram: Optional[KirbyAMRamSpec] = None
        self._poc: Optional[_POCConfig] = None

        # Local state to avoid spamming checks
        self._last_room_id: Optional[int] = None
        self._sent_goal: bool = False

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        """
        Optional but recommended. If you add a ROM hash/signature to ram.yaml,
        validate it here to prevent users from connecting the wrong game.
        """
        return True

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.slot_data is None or ctx.slot is None:
            return

        # Load ram.yaml once
        if self._ram is None:
            self._ram = load_ram_spec()

        # Build POC config once using slot_data + your YAML naming conventions.
        # Keep this stable and boring; avoid hard-coding IDs if slot_data can provide them.
        if self._poc is None:
            # You can also choose to embed these in slot_data from fill_slot_data().
            self._poc = _POCConfig(
                room_check_location_name=ctx.slot_data.get("poc_room_check_location", "POC: Enter Room (Check)"),
                victory_location_name=ctx.slot_data.get("poc_victory_location", "Victory"),
                room_check_room_id=int(ctx.slot_data.get("poc_room_check_room_id", 0)),
                goal_room_id=int(ctx.slot_data.get("poc_goal_room_id", 0)),
                max_health_item_name=ctx.slot_data.get("poc_max_health_item", "Max Health Up"),
                phone_charge_item_name=ctx.slot_data.get("poc_phone_charge_item", "Charge Cell Phone"),
            )

        ram = self._ram
        poc = self._poc

        # Resolve name->id via server slot_data mappings (best practice).
        # Your world can include these mappings in fill_slot_data() to avoid re-deriving them here.
        name_to_loc_id: dict[str, int] = ctx.slot_data.get("location_name_to_id", {})
        name_to_item_id: dict[str, int] = ctx.slot_data.get("item_name_to_id", {})

        room_check_loc_id = name_to_loc_id.get(poc.room_check_location_name)
        victory_loc_id = name_to_loc_id.get(poc.victory_location_name)

        # --- Read current room id ---
        # Use guards so you never read garbage if the ROM state isn't “in-game”.
        room_id_bytes = await self.read(
            ctx,
            [(ram.room_id.domain, ram.room_id.address, ram.room_id.size)],
            ram.guards,
        )
        if not room_id_bytes:
            return

        room_id = memory.unpack_uint16(room_id_bytes[0]) if ram.room_id.size == 2 else memory.unpack_uint8(room_id_bytes[0])

        # --- Location check on entering a specific room ---
        if (
            room_check_loc_id is not None
            and room_id != self._last_room_id
            and room_id == poc.room_check_room_id
        ):
            await ctx.check_locations({room_check_loc_id})

        # --- Goal when entering goal room ---
        if not self._sent_goal and room_id == poc.goal_room_id:
            self._sent_goal = True

            # Option A: Mark a dedicated Victory location checked (recommended if your world uses an event item).
            if victory_loc_id is not None:
                await ctx.check_locations({victory_loc_id})

            # Option B: Also send status update (harmless even if you use Victory event logic).
            await ctx.send_msgs([{
                "cmd": "StatusUpdate",
                "status": ClientStatus.CLIENT_GOAL,
            }])
            ctx.finished_game = True

        self._last_room_id = room_id

        # --- Apply received items ---
        # “BizHawkClient” provides item reception tracking via ctx.items_received.
        # Keep it minimal: apply the delta since last loop.
        await self._apply_received_items(ctx, ram, poc, name_to_item_id)

    async def _apply_received_items(
        self,
        ctx: BizHawkClientContext,
        ram: KirbyAMRamSpec,
        poc: _POCConfig,
        name_to_item_id: dict[str, int],
    ) -> None:
        if ctx.items_received is None:
            return

        # Track how many we’ve applied already.
        applied = getattr(ctx, "_kirbyam_items_applied", 0)
        if applied >= len(ctx.items_received):
            return

        new_items = ctx.items_received[applied:]
        setattr(ctx, "_kirbyam_items_applied", len(ctx.items_received))

        for net_item in new_items:
            # net_item.item is the numeric item id.
            # We map by name for readability via slot_data map inversion.
            # If you prefer, store an id->action map in slot_data.
            item_name = None
            # Invert mapping lazily (small POC scale; fine).
            for n, iid in name_to_item_id.items():
                if iid == net_item.item:
                    item_name = n
                    break

            if item_name == poc.max_health_item_name:
                await self._give_max_health(ctx, ram)
            elif item_name == poc.phone_charge_item_name:
                await self._give_phone_charge(ctx, ram)
            else:
                # Unknown or filler you haven't implemented: ignore safely.
                pass

    async def _give_max_health(self, ctx: BizHawkClientContext, ram: KirbyAMRamSpec) -> None:
        """
        Example: increment max HP by 1 (or whatever your ram.yaml defines).
        """
        cur_bytes = await self.read(
            ctx,
            [(ram.max_hp.domain, ram.max_hp.address, ram.max_hp.size)],
            ram.guards,
        )
        if not cur_bytes:
            return

        cur = memory.unpack_uint8(cur_bytes[0]) if ram.max_hp.size == 1 else memory.unpack_uint16(cur_bytes[0])
        new = min(cur + 1, ram.max_hp.max_value)

        await self.write(
            ctx,
            [(ram.max_hp.domain, ram.max_hp.address, memory.pack_uint8(new) if ram.max_hp.size == 1 else memory.pack_uint16(new))],
            ram.guards,
        )

    async def _give_phone_charge(self, ctx: BizHawkClientContext, ram: KirbyAMRamSpec) -> None:
        """
        Optional: increment a “phone charge” counter.
        If you don't have a real RAM concept yet, you can no-op safely.
        """
        if ram.phone_charge is None:
            return

        cur_bytes = await self.read(
            ctx,
            [(ram.phone_charge.domain, ram.phone_charge.address, ram.phone_charge.size)],
            ram.guards,
        )
        if not cur_bytes:
            return

        cur = memory.unpack_uint8(cur_bytes[0])
        new = min(cur + 1, ram.phone_charge.max_value)

        await self.write(
            ctx,
            [(ram.phone_charge.domain, ram.phone_charge.address, memory.pack_uint8(new))],
            ram.guards,
        )
