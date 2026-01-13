from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data
from .bases import KirbyAMTestBase


class TestKirbyAMPOCLocations(KirbyAMTestBase):
    def test_has_poc_locations_in_yaml(self) -> None:
        data = load_kirbyam_data()
        poc_locations = {name for row in data.locations if "poc" in row.get("tags", []) and (name := row.get("name")) is not None}
        assert len(poc_locations) > 0, "No locations tagged 'poc' in locations.yaml"

    def test_poc_locations_exist_in_world(self) -> None:
        self.world_setup()

        data = load_kirbyam_data()
        expected = {name for row in data.locations if "poc" in row.get("tags", []) and (name := row.get("name")) is not None}

        world_locations = {loc.name for loc in self.multiworld.get_locations(self.player)}

        missing = expected - world_locations
        assert not missing, f"POC locations missing from generated world: {sorted(missing)}"

    def test_poc_locations_not_in_origin_region(self) -> None:
        self.world_setup()

        # Collect locations attached to Menu (origin)
        menu = self.multiworld.get_region("Menu", self.player)
        menu_loc_names = {loc.name for loc in menu.locations}

        data = load_kirbyam_data()
        poc_locations = {name for row in data.locations if "poc" in row.get("tags", []) and (name := row.get("name")) is not None}

        # POC locations should be in Main/Branch, not Menu (Menu only has Victory event)
        bad = poc_locations & menu_loc_names
        assert not bad, f"POC locations unexpectedly placed in Menu: {sorted(bad)}"
