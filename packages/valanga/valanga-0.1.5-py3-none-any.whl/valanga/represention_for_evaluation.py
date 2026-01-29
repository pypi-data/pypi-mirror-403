"""
Contains the definition of the ContentRepresentation protocol for content representations used in evaluations.
"""

from typing import Any, Protocol, TypeVar

from .evaluator_types import EvaluatorInput
from .game import State

StateT_contra = TypeVar("StateT_contra", bound=State, contravariant=True, default=Any)


class ContentRepresentation(Protocol[StateT_contra]):
    """
    Protocol defining the interface for a content representation.
    It is a function returning the proper input for evaluation by the content evaluator.
    """

    def get_evaluator_input(self, state: StateT_contra) -> EvaluatorInput:
        """
        Returns the evaluator input tensor for the content. Content representations have generally a compressed view and complemetary view of state info so to avoid redundancy and have all the necessary info we also give the state as input.

        Args:
            state: The current state of the game.

        Returns:
            The evaluator input tensor.
        """
