from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data


def test_data_loader_smoke() -> None:
    data = load_kirbyam_data()
    assert data.schema_version >= 1
    assert len(data.items) >= 0
    assert len(data.locations) >= 0
    assert len(data.goals) >= 0
