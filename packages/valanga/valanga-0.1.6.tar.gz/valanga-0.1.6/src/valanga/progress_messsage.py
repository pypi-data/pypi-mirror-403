"""
Module for the ProgressMessage class.
"""

from dataclasses import dataclass

from .game import Color


@dataclass
class PlayerProgressMessage:
    """
    Represents a message containing evaluation information.

    Attributes:
        evaluation_stock (Any): The evaluation for the stock.
    """

    progress_percent: int | None
    player_color: Color
