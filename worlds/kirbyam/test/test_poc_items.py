from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data
from .bases import KirbyAMTestBase


class TestKirbyAMPOCItems(KirbyAMTestBase):
    def test_has_poc_items_in_yaml(self) -> None:
        data = load_kirbyam_data()
        poc_items = [row["name"] for row in data.items if "poc" in row.get("tags", [])]
        assert len(poc_items) > 0, "No items tagged 'poc' in items.yaml"

    def test_poc_item_count_matches_poc_location_count(self) -> None:
        data = load_kirbyam_data()
        poc_items = [row["name"] for row in data.items if "poc" in row.get("tags", []) and row.get("name") is not None]
        poc_locations = [row.get("name") for row in data.locations if "poc" in row.get("tags", []) and row.get("name") is not None]
        poc_locations = [name for name in poc_locations if name is not None]
        assert len(poc_items) == len(poc_locations), "POC requires item count == location count"

    def test_itempool_contains_all_poc_items(self) -> None:
        self.world_setup()

        data = load_kirbyam_data()
        expected = {row["name"] for row in data.items if "poc" in row.get("tags", [])}

        pool = {item.name for item in self.multiworld.itempool if item.player == self.player}

        missing = expected - pool
        assert not missing, f"POC items missing from itempool: {sorted(missing)}"
