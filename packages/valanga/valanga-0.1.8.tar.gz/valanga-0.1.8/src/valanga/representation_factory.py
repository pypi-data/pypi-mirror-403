"""
Factory for creating content representations from game states and state modifications.
"""

from dataclasses import dataclass
from typing import Protocol

from .game import State


class CreateFromState[StateT: State, RepT](Protocol):
    """
    Protocol for creating a state representation from a state.
    """

    def __call__(self, state: StateT) -> RepT: ...


class CreateFromStateAndModifications[StateT: State, StateModT, RepT](Protocol):
    """
    Protocol for creating a state representation from a state and modifications.
    """

    def __call__(
        self,
        state: StateT,
        state_modifications: StateModT,
        previous_state_representation: RepT,
    ) -> RepT: ...


@dataclass
class RepresentationFactory[StateT: State, StateModT, RepT]:
    """Factory for creating content representations from states and state modifications.
    Attributes:
        create_from_state: Function to create a content representation from a state.
        create_from_state_and_modifications: Function to create a content representation from a state and state modifications.
    """

    create_from_state: CreateFromState[StateT, RepT]
    create_from_state_and_modifications: CreateFromStateAndModifications[
        StateT, StateModT, RepT
    ]

    def create_from_transition(
        self,
        state: StateT,
        previous_state_representation: RepT | None,
        modifications: StateModT | None,
    ) -> RepT:
        """Creates a content representation from a state transition.
        Args:
            state: The current state of the game.
            previous_state_representation: The content representation of the previous state, or None if not available.
            modifications: The modifications applied to the previous state to reach the current state, or None if not available.
        Returns:
            ContentRepresentation[StateT, EvalIn]: The content representation of the current state.
        """
        if previous_state_representation is None or modifications is None:
            return self.create_from_state(state)
        return self.create_from_state_and_modifications(
            state, modifications, previous_state_representation
        )
