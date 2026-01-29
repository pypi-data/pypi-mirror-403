"""
Factory class for creating state representations.
"""

from dataclasses import dataclass
from typing import Protocol

from .game import State, StateModifications
from .represention_for_evaluation import ContentRepresentation


class CreateFromState[StateT: State, RepT: ContentRepresentation](Protocol):
    """
    Protocol for creating a state representation from a state.
    """

    def __call__(self, state: StateT) -> RepT: ...


class CreateFromStateAndModifications[StateT: State, RepT: ContentRepresentation](
    Protocol
):
    """
    Protocol for creating a state representation from a state and modifications.
    """

    def __call__(
        self,
        state: StateT,
        state_modifications: StateModifications,
        previous_state_representation: RepT,
    ) -> RepT: ...


@dataclass
class RepresentationFactory[StateT: State, RepT: ContentRepresentation]:
    """
    Factory class for creating state representations.
    """

    create_from_state: CreateFromState[StateT, RepT]
    create_from_state_and_modifications: CreateFromStateAndModifications[StateT, RepT]

    def create_from_transition(
        self,
        state: StateT,
        previous_state_representation: RepT | None,
        modifications: StateModifications | None,
    ) -> RepT:
        """
        Create a Generic T_StateRepresentation object from a transition.

        Args:
            state (State): The current state of the game.
            previous_state_representation (Representation364 | None): The representation of the previous state. None if this is the root node.
            modifications (StateModifications | None): The modifications from the parent state to the current state. None if this is the root node.

        Returns:
            T_StateRepresentation: The created (Generic) Representation object

        This version is supposed to be faster as it only modifies the previous state
        representation with the last modification
        """
        if previous_state_representation is None:  # this is the root_node
            representation = self.create_from_state(state=state)
        else:
            if modifications is None:
                representation = self.create_from_state(state=state)
            else:
                representation = self.create_from_state_and_modifications(
                    state=state,
                    state_modifications=modifications,
                    previous_state_representation=previous_state_representation,
                )

        return representation
