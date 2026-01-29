"""
Factory for creating content representations from game states and state modifications.
"""

from dataclasses import dataclass
from typing import Callable, TypeVar

from .game import State, StateModifications
from .represention_for_evaluation import ContentRepresentation

StateT = TypeVar("StateT", bound=State)
EvalIn = TypeVar("EvalIn")

CreateFromState = Callable[[StateT], ContentRepresentation[StateT, EvalIn]]
CreateFromStateAndMods = Callable[
    [StateT, StateModifications, ContentRepresentation[StateT, EvalIn]],
    ContentRepresentation[StateT, EvalIn],
]


@dataclass
class RepresentationFactory[StateT: State, EvalIn]:
    """Factory for creating content representations from states and state modifications.
    Attributes:
        create_from_state: Function to create a content representation from a state.
        create_from_state_and_modifications: Function to create a content representation from a state and state modifications.
    """

    create_from_state: CreateFromState[StateT, EvalIn]
    create_from_state_and_modifications: CreateFromStateAndMods[StateT, EvalIn]

    def create_from_transition(
        self,
        state: StateT,
        previous_state_representation: ContentRepresentation[StateT, EvalIn] | None,
        modifications: StateModifications | None,
    ) -> ContentRepresentation[StateT, EvalIn]:
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
