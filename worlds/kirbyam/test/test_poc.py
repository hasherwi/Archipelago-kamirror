from __future__ import annotations

from .bases import KamirrorTestBase


class TestKamirrorPOCSmoke(KamirrorTestBase):
    def test_can_generate(self) -> None:
        # If world construction or generation fails, this test will fail automatically.
        self.world_setup()

    def test_has_expected_locations(self) -> None:
        self.world_setup()
        loc_names = {loc.name for loc in self.multiworld.get_locations(self.player)}
        assert "Test Location 1" in loc_names
        assert "Test Location 2" in loc_names
        assert "Victory" in loc_names  # event location

    def test_completion_condition_exists(self) -> None:
        self.world_setup()
        assert self.multiworld.completion_condition[self.player] is not None
