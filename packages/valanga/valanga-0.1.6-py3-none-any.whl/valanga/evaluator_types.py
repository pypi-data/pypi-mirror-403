"""Small shared types used by evaluators and representations.

This module exists to avoid runtime circular imports between `evaluations` and
`represention_for_evaluation`.
"""

from typing import Annotated

EvaluatorInput = Annotated[
    object, "The input type for the evaluator, typically a tensor or array"
]

__all__ = ["EvaluatorInput"]
