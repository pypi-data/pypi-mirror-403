"""
Evaluation-related classes and types.
"""

from dataclasses import dataclass
from typing import Protocol

from .game import BranchKey, State
from .over_event import OverEvent
from .represention_for_evaluation import ContentRepresentation


class EvalItem[StateT: State](Protocol):
    """
    The protocol for an evaluation item.
    An evaluation item is something that has a state and optionally a representation of that state.
    """

    @property
    def state(self) -> StateT:
        """The state associated with this evaluation item."""
        ...

    @property
    def state_representation(self) -> ContentRepresentation | None:
        """The representation of the state associated with this evaluation item, if available."""
        ...


@dataclass
class ForcedOutcome:
    """
    The class
    """

    # The forced outcome with optimal play by both sides.
    outcome: OverEvent

    # the line
    line: list[BranchKey]


@dataclass
class FloatyStateEvaluation:
    """
    The class to defines what is an evaluation of a board.
    By convention is it always evaluated from the view point of the white side.
    """

    # The evaluation value for the white side when the outcome is not certain. Typically, a float.
    # todo can we remove the None option?
    value_white: float | None


StateEvaluation = FloatyStateEvaluation | ForcedOutcome
