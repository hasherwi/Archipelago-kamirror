from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data


def test_poc_items_not_more_than_poc_locations() -> None:
    data = load_kirbyam_data()
    poc_items = [row["name"] for row in data.items if "poc" in row.get("tags", [])]
    poc_locations = [row.get("name", "") for row in data.locations if "poc" in row.get("tags", [])]

    assert len(poc_items) <= len(poc_locations), (
        f"POC requires item count <= location count "
        f"(poc_items={len(poc_items)}, poc_locations={len(poc_locations)})"
    )

    if len(poc_items) < len(poc_locations):
        filler_candidates = [
            row["name"]
            for row in data.items
            if "poc" in row.get("tags", []) and (row.get("classification") or "").strip().lower() == "filler"
        ]
        assert len(filler_candidates) == 1, (
            "POC padding requires exactly one item tagged 'poc' with classification 'filler' in items.yaml. "
            f"Found {len(filler_candidates)}: {filler_candidates}"
        )

