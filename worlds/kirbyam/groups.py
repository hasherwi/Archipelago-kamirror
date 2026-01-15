from typing import Dict, Set

from .data import LocationCategory, data


# Item Groups
ITEM_GROUPS: Dict[str, Set[str]] = {}

for item in data.items.values():
    for tag in item.tags:
        if tag not in ITEM_GROUPS:
            ITEM_GROUPS[tag] = set()
        ITEM_GROUPS[tag].add(item.label)

# Location Groups
_LOCATION_GROUP_MAPS = {
    "0. Game Start": {
        "MAP_GAME_START",
    },
    "1. Rainbow Route": {
        "MAP_RAINBOW_ROUTE",
    },
    "2. Moonlight Mansion": {
        "MAP_MOONLIGHT_MANSION",
    },
    "3. Cabbage Cavern": {
        "MAP_CABBAGE_CAVERN",
    },
    "4. Mustard Mountain": {
        "MAP_MUSTARD_MOUNTAIN",
    },
    "5. Carrot Castle": {
        "MAP_CARROT_CASTLE",
    },
    "6. Olive Ocean": {
        "MAP_OLIVE_OCEAN",
    },
    "7. Peppermint Palace": {
        "MAP_PEPPERMINT_PALACE",
    },
    "8. Radish Ruins": {
        "MAP_RADISH_RUINS",
    },
    "9. Candy Constellation": {
        "MAP_CANDY_CONSTELLATION",
    },
    "10. Dimension Mirror": {
        "MAP_DIMENSION_MIRROR",
    },
}

_LOCATION_CATEGORY_TO_GROUP_NAME = {
    LocationCategory.SHARD: "Mirror Shards",
}

LOCATION_GROUPS: Dict[str, Set[str]] = {group_name: set() for group_name in _LOCATION_CATEGORY_TO_GROUP_NAME.values()}
for location in data.locations.values():
    # Category groups
    LOCATION_GROUPS[_LOCATION_CATEGORY_TO_GROUP_NAME[location.category]].add(location.label)

    # Tag groups
    for tag in location.tags:
        if tag not in LOCATION_GROUPS:
            LOCATION_GROUPS[tag] = set()
        LOCATION_GROUPS[tag].add(location.label)

# Meta-groups
LOCATION_GROUPS["Areas"] = {
    *LOCATION_GROUPS.get("0. Game Start", set()),
    *LOCATION_GROUPS.get("1. Rainbow Route", set()),
    *LOCATION_GROUPS.get("2. Moonlight Mansion", set()),
    *LOCATION_GROUPS.get("3. Cabbage Cavern", set()),
    *LOCATION_GROUPS.get("4. Mustard Mountain", set()),
    *LOCATION_GROUPS.get("5. Carrot Castle", set()),
    *LOCATION_GROUPS.get("6. Olive Ocean", set()),
    *LOCATION_GROUPS.get("7. Peppermint Palace", set()),
    *LOCATION_GROUPS.get("8. Radish Ruins", set()),
    *LOCATION_GROUPS.get("9. Candy Constellation", set()),
    *LOCATION_GROUPS.get("10. Dimension Mirror", set()),
}
