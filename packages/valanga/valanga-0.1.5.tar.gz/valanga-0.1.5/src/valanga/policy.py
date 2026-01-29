"""
Policy-related classes and protocols for branch selection in game trees.
"""

from dataclasses import dataclass
from typing import Mapping, Protocol

from valanga.evaluations import StateEvaluation
from valanga.game import BranchKey, BranchName, Seed, State


@dataclass(frozen=True, slots=True)
class BranchPolicy:
    """
    Represents a probability distribution over branches.
    """

    probs: Mapping[BranchKey, float]  # should sum to ~1.0


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A recommendation for a specific branch in a tree node."""

    recommended_name: BranchName
    evaluation: StateEvaluation | None = None
    policy: BranchPolicy | None = None
    branch_evals: Mapping[BranchName, StateEvaluation] | None = None


class BranchSelector(Protocol):
    """Protocol for a branch selector."""

    def recommend(self, state: State, seed: Seed) -> Recommendation:
        """Given a state and a seed, recommends a branch to take.
        Args:
            state (State): The current state of the game.
            seed (Seed): A seed for any randomness involved in the selection.
        Returns:
            Recommendation: The recommended branch to take.
        """
        ...
