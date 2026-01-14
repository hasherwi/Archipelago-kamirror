from __future__ import annotations

from typing import Any, Dict, Optional, List, Mapping

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from .data_loader import load_kirbyam_data, KirbyAMData
from .id_map import build_id_map
from .logging_utils import log_event, log_debug

GAME_NAME = "Kirby & The Amazing Mirror"
ORIGIN_REGION = "Menu"


class KirbyAMWebWorld(WebWorld):
    game = GAME_NAME
    game_info_languages = ["en"]
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="How to set up and play Kirby & The Amazing Mirror in Archipelago (POC).",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["Harrison"],
        )
    ]
    bug_report_page = None


class KirbyAMWorld(World):
    """
    Minimal POC world:

    - Regions: Menu -> Main Area -> Test Branch
    - Locations: all YAML locations tagged 'poc' become real AP locations (address != None)
    - Victory: separate *event* location (address None) containing *event* item (code None)
    - Items: all YAML items tagged 'poc' are in the pool; pad with exactly one configured filler item as needed
    """

    # ----- Required by AutoWorld metaclass -----
    item_name_to_id: Dict[str, int] = {}
    location_name_to_id: Dict[str, int] = {}

    game = GAME_NAME
    web = KirbyAMWebWorld()
    origin_region_name = ORIGIN_REGION

    # Deterministic base IDs. Do not change once you have public releases.
    _base_location_id = 23_450_000
    _base_item_id = 23_460_000

    # ----- Instance state -----
    _data: KirbyAMData
    _poc_location_names: List[str]
    _poc_item_names: List[str]
    _poc_padding_item_name: Optional[str]
    _goal_location_name: Optional[str]

    # Event naming (tests rely on these names)
    _VICTORY_LOCATION_NAME = "Victory"
    _VICTORY_ITEM_NAME = "Victory"

    def _log_ctx(self) -> dict[str, object]:
        mw = getattr(self, "multiworld", None)
        return {
            "player": getattr(self, "player", None),
            "player_name": getattr(mw, "player_name", {}).get(self.player) if mw else None,
            "seed": getattr(mw, "seed_name", None) if mw else None,
            "game": getattr(self, "game", None),
            "world_id": id(self),
        }

    @staticmethod
    def _class_from_str(value: str | None) -> ItemClassification:
        if not value:
            return ItemClassification.filler
        v = value.strip().lower()
        if v == "progression":
            return ItemClassification.progression
        if v == "useful":
            return ItemClassification.useful
        if v == "trap":
            return ItemClassification.trap
        return ItemClassification.filler

    @staticmethod
    def _tags(row: Mapping[str, object]) -> List[str]:
        tags = row.get("tags", [])
        if isinstance(tags, list):
            return [str(t) for t in tags]
        return []

    def generate_early(self) -> None:
        log_event("generate_early.start", **self._log_ctx())

        self._data = load_kirbyam_data()
        data = self._data

        # ensure instance-local dicts
        self.item_name_to_id = dict(self.item_name_to_id)
        self.location_name_to_id = dict(self.location_name_to_id)

        log_event(
            "generate_early.data_loaded",
            **self._log_ctx(),
            items=len(data.items),
            locations=len(data.locations),
            goals=len(data.goals),
        )

        # Build deterministic key->id maps
        item_key_to_id = build_id_map(
            (row["key"] for row in data.items if "key" in row),
            base_id=self._base_item_id,
            namespace="kirbyam:item",
        )
        loc_key_to_id = build_id_map(
            (row["key"] for row in data.locations if "key" in row),
            base_id=self._base_location_id,
            namespace="kirbyam:location",
        )

        # Build name->id maps
        self.item_name_to_id = {
            str(row["name"]): item_key_to_id[str(row["key"])]
            for row in data.items
            if "key" in row and "name" in row
        }
        self.location_name_to_id = {
            str(row["name"]): loc_key_to_id[str(row["key"])]
            for row in data.locations
            if "key" in row and "name" in row
        }

        # POC selection by tags (no hard-coded keys)
        self._poc_location_names = [
            str(row["name"])
            for row in data.locations
            if "name" in row and "poc" in self._tags(row)
        ]
        self._poc_item_names = [
            str(row["name"])
            for row in data.items
            if "name" in row and "poc" in self._tags(row)
        ]

        log_event(
            "generate_early.poc_sets",
            **self._log_ctx(),
            poc_items=len(self._poc_item_names),
            poc_locations=len(self._poc_location_names),
        )

        if not self._poc_location_names:
            raise ValueError("No locations tagged 'poc' found in locations.yaml")
        if not self._poc_item_names:
            raise ValueError("No items tagged 'poc' found in items.yaml")

        # Validate names exist in the ID maps
        missing_loc_ids = [n for n in self._poc_location_names if n not in self.location_name_to_id]
        missing_item_ids = [n for n in self._poc_item_names if n not in self.item_name_to_id]
        if missing_loc_ids:
            raise ValueError(f"POC locations missing from location_name_to_id: {missing_loc_ids}")
        if missing_item_ids:
            raise ValueError(f"POC items missing from item_name_to_id: {missing_item_ids}")

        # Identify the "goal" location (optional but recommended)
        goal_locs = [
            str(row["name"])
            for row in data.locations
            if "name" in row and "poc" in self._tags(row) and "goal" in self._tags(row)
        ]
        self._goal_location_name = goal_locs[0] if goal_locs else None

        # Choose exactly one padding item: tagged 'poc' and classification == filler
        filler_candidates = [
            str(row["name"])
            for row in data.items
            if "name" in row and "poc" in self._tags(row)
            and (str(row.get("classification", "")).strip().lower() == "filler")
        ]
        if len(filler_candidates) != 1:
            raise ValueError(
                "POC padding requires exactly one item tagged 'poc' with classification 'filler' in items.yaml. "
                f"Found {len(filler_candidates)}: {filler_candidates}"
            )
        self._poc_padding_item_name = filler_candidates[0]

        log_event(
            "generate_early.poc_contract",
            **self._log_ctx(),
            goal_location=self._goal_location_name,
            padding_item=self._poc_padding_item_name,
        )

        log_event("generate_early.done", **self._log_ctx())

    def create_regions(self) -> None:
        log_event("create_regions.start", **self._log_ctx())

        # Regions required by tests
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        main = Region("Main Area", self.player, self.multiworld)
        branch = Region("Test Branch", self.player, self.multiworld)

        self.multiworld.regions += [menu, main, branch]

        # Connect such that branch is reachable with no items
        menu.connect(main, "To Main Area")
        main.connect(branch, "To Test Branch")

        # Victory *event* location in Menu (address None)
        victory_loc = Location(self.player, self._VICTORY_LOCATION_NAME, None, menu)
        victory_loc.place_locked_item(self._create_event_item(self._VICTORY_ITEM_NAME))
        menu.locations.append(victory_loc)

        # Place POC locations across regions (none locked; these must be fillable)
        poc_locations = list(self._poc_location_names)
        split = max(1, len(poc_locations) // 2)
        main_locs = poc_locations[:split]
        branch_locs = poc_locations[split:]

        for loc_name in main_locs:
            main.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], main))
        for loc_name in branch_locs:
            branch.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], branch))

        log_debug(
            "create_regions.poc_distribution",
            **self._log_ctx(),
            main_count=len(main_locs),
            branch_count=len(branch_locs),
        )

        log_event(
            "create_regions.done",
            **self._log_ctx(),
            regions=3,
            poc_locations=len(poc_locations),
        )

    def create_items(self) -> None:
        log_event("create_items.start", **self._log_ctx())

        # Build pool from all POC items
        pool_names = list(self._poc_item_names)

        # Pad to match *fillable* location count (exclude Victory event)
        fillable_locations = len(self._poc_location_names)
        needed = fillable_locations - len(pool_names)

        if needed > 0:
            assert self._poc_padding_item_name is not None
            pool_names.extend([self._poc_padding_item_name] * needed)
        elif needed < 0:
            raise ValueError(
                "POC requires items <= locations (Victory is an event and not fillable). "
                f"poc_items={len(self._poc_item_names)} poc_locations={fillable_locations}"
            )

        for item_name in pool_names:
            self.multiworld.itempool.append(self.create_item(item_name))

        log_event(
            "create_items.done",
            **self._log_ctx(),
            pool_items=len(pool_names),
            padded=max(0, len(pool_names) - len(self._poc_item_names)),
        )

    def set_rules(self) -> None:
        log_event("set_rules.start", **self._log_ctx())

        # Completion is based on collecting the Victory event item
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has(self._VICTORY_ITEM_NAME, self.player)
        )

        log_event("set_rules.done", **self._log_ctx(), completion=self._VICTORY_ITEM_NAME)

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        row = next((r for r in self._data.items if str(r.get("name")) == name), None)
        classification = self._class_from_str(str(row.get("classification")) if row else None)
        return Item(name, classification, item_id, self.player)

    def _create_event_item(self, name: str) -> Item:
        # code=None is correct for event items; must only be placed at address=None locations
        return Item(name, ItemClassification.progression, None, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        return {}
