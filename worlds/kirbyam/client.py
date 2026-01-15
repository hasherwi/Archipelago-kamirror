"""BizHawk client for Kirby & The Amazing Mirror.

This is a minimal scaffold so the world can be loaded and a seed can be
generated while ROM integration is still under construction.

To progress this into a functional client you will need to:
  - Define ROM validation (ROM name/version string check)
  - Read the per-seed auth token from a ROM address (see data/addresses.json)
  - Read location-check state from RAM (e.g., a bitfield)
  - Write received items into RAM (or a queue consumed by injected code)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from .data import data

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext


class KirbyAmClient(BizHawkClient):
    game = "Kirby & The Amazing Mirror"
    patch_suffix = ".apkirbyam"

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        """Return True if the currently loaded ROM appears to be Kirby AM.

        Until a Kirby-specific base patch is in place, we only check that we can
        talk to BizHawk; no robust ROM identification is performed.
        """
        _ = ctx
        return True

    async def get_payload(self, ctx: "BizHawkClientContext") -> Optional[dict]:
        """Provide additional payload data for the server connection.

        Once ROM integration is ready, read an auth token from ROM and return:
            {"auth": <base64 string>}
        """
        _ = ctx
        return None

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        """Main polling loop.

        This is where you'll later:
          - detect newly checked locations and call ctx.send_msgs([...])
          - deliver received items by writing to game memory
        """
        while not ctx.exit_event.is_set():
            await asyncio.sleep(0.5)


# Registration helper for BizHawk integration
bizhawk.register_client(KirbyAmClient)
