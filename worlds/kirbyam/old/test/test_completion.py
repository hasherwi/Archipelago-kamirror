from __future__ import annotations

from .bases import KirbyAMTestBase


class TestKirbyAMCompletion(KirbyAMTestBase):
    def test_completion_condition_registered(self) -> None:
        self.world_setup()
        assert self.player in self.multiworld.completion_condition

    def test_completion_condition_uses_victory_event_item(self) -> None:
        self.world_setup()
        state = self.multiworld.state

        # Not complete at start
        assert not self.multiworld.completion_condition[self.player](state)

        # Collect the locked event item from the Victory location
        victory_loc = self.multiworld.get_location("Victory", self.player)
        assert victory_loc.item is not None, "Victory location should have a locked event item"

        state.collect(victory_loc.item)

        assert self.multiworld.completion_condition[self.player](state)
