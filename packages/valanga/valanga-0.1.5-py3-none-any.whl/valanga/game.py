"""
Common types and utilities representing game objects shared by multiple libraries.
"""

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Iterator, Protocol, Self, Sequence, TypeVar

type Seed = Annotated[int, "seed"]

type StateTag = Annotated[Hashable, "A label or identifier for a state in a game"]

type StateModifications = Annotated[
    object, "Modifications to the state between to time steps of the game"
]  # used for time and memory optimisation

type BranchName = Annotated[str, "A human-readable name for a branch of a state"]

type BranchKey = Annotated[Hashable, "A label or identifier for a branch in a tree"]
type ActionName = Annotated[str, "A human-readable name for an action of a state"]

type ActionKey = Annotated[Hashable, "A label or identifier for an action"]

T_co = TypeVar("T_co", bound=Hashable, covariant=True)


class BranchKeyGeneratorP(Protocol[T_co]):
    """Protocol for a branch key generator that yields branch keys."""

    # whether to sort the branch keys by their respective uci for easy comparison of various implementations
    sort_branch_keys: bool = False

    @property
    def all_generated_keys(self) -> Sequence[T_co] | None:
        """Returns all generated branch keys if available, otherwise None."""
        ...

    def __iter__(self) -> Iterator[T_co]:
        """Returns an iterator over the branch keys."""
        ...

    def __next__(self) -> T_co:
        """Returns the next branch key."""
        ...

    def more_than_one(self) -> bool:
        """Checks if there is more than one branch available.

        Returns:
            bool: True if there is more than one branch, False otherwise.
        """
        ...

    def get_all(self) -> Sequence[T_co]:
        """Returns a list of all branch keys."""
        ...

    def copy_with_reset(self) -> Self:
        """Creates a copy of the legal move generator with an optional reset of generated moves.

        Returns:
            Self: A new instance of the legal move generator with the specified generated moves.
        """
        ...


class State(Protocol):
    """Protocol for a content object that has a tag."""

    @property
    def tag(self) -> StateTag:
        """Returns the tag of the content.

        Returns:
            StateTag: The tag of the content.
        """
        ...

    @property
    def branch_keys(self) -> BranchKeyGeneratorP[BranchKey]:
        """Returns the branch keys associated with the content.

        Returns:
            BranchKeyGeneratorP: The branch keys associated with the content.
        """
        ...

    def branch_name_from_key(self, key: BranchKey) -> str:
        """Returns the branch name corresponding to the given branch key.

        Args:
            key (BranchKey): The branch key.

        Returns:
            str: The branch name corresponding to the given branch key.
        """
        ...

    def branch_key_from_name(self, name: str) -> BranchKey:
        """Returns the branch key corresponding to the given branch name.

        Args:
            name (str): The branch name.
        Returns:
            BranchKey: The branch key corresponding to the given branch name.
        """
        ...

    def is_game_over(self) -> bool:
        """Checks if the game represented by the content is over.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        ...

    def copy(self, stack: bool, deep_copy_legal_moves: bool = True) -> Self:
        """
        Create a copy of the current board.

        Args:
            stack (bool): Whether to copy the previous action stack as well. Important in some games.
            deep_copy_legal_moves (bool): Whether to deep copy the legal moves generator.

        Returns:
            BoardChi: A new instance of the BoardChi class with the copied board.
        """
        ...

    def step(self, branch_key: BranchKey) -> StateModifications | None:
        """Advances the state by applying the action corresponding to the given branch key.

        Args:
            branch_key (BranchKey): The branch key representing the action to be applied.

        Returns:
            StateModifications | None: The modifications to the state after applying the action, or None if the action is invalid.
        """
        ...

    def pprint(self) -> str:
        """Returns a pretty-printed string representation of the content.

        Returns:
            str: A pretty-printed string representation of the content.
        """
        ...


type ColorIndex = Annotated[int, "1 for white, 0 for black"]

WHITE: ColorIndex = 1
BLACK: ColorIndex = 0


class Color(int, Enum):
    """Represents the color of a player in a game."""

    WHITE = WHITE
    BLACK = BLACK


def _actions_history_factory() -> list[ActionKey]:
    return []


@dataclass
class StatePlusHistory[StateT]:
    """A State with historical actions and states."""

    @staticmethod
    def _states_factory() -> list[StateT]:
        return []

    current_state_tag: StateTag
    historical_actions: list[ActionKey] = field(
        default_factory=_actions_history_factory
    )
    historical_states: list[StateT] = field(default_factory=_states_factory)


class HasTurn(Protocol):
    """Protocol for a content object that has a tag."""

    @property
    def turn(self) -> Color:
        """Returns the tag of the content.

        Returns:
            ContentTag: The tag of the content.
        """
        ...


class TurnState(State, HasTurn, Protocol):
    """A State that also supports turn()."""

    ...


@dataclass
class TurnStatePlusHistory[StateT = Any]:
    """A TurnState with historical actions and states."""

    @staticmethod
    def _states_factory() -> list[StateT]:
        return []

    current_state_tag: StateTag
    turn: Color
    historical_actions: list[ActionKey] = field(
        default_factory=_actions_history_factory
    )
    historical_states: list[StateT] = field(default_factory=_states_factory)
