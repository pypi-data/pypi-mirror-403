# valanga

![Python 3.13](https://img.shields.io/badge/python-3.13-blue?logo=python)
[![Tests](https://github.com/victorgabillon/valanga/actions/workflows/ci.yaml/badge.svg?label=tests)](https://github.com/victorgabillon/valanga/actions/workflows/ci.yaml)
[![License: GPL v3](https://img.shields.io/github/license/victorgabillon/valanga)](LICENSE)

Shared Python types and lightweight utilities for describing turn-based games and their evaluations. The package exposes protocols for representing states, outcomes, and state representations that other libraries can build on.

## Key concepts
- **Game primitives**: `Color`, `BranchKey`, `State`, and related protocols describe whose turn it is, how to enumerate legal branches, and how to copy or advance a state. 【F:src/valanga/game.py†L14-L95】
- **Evaluations**: `FloatyStateEvaluation` captures heuristic scores while `ForcedOutcome` records a definitive result plus the line of play that forces it. Both are grouped under `BoardEvaluation`. 【F:src/valanga/evaluations.py†L13-L43】
- **Game termination**: `OverEvent` combines how a game ended with who won, backed by `HowOver` and `Winner` enums. Utility helpers like `is_over()` and `get_over_tag()` simplify downstream checks. 【F:src/valanga/over_event.py†L8-L115】
- **State representations**: `ContentRepresentation` defines how to turn a `State` into evaluator input, and `RepresentationFactory` builds or updates those representations from states and modifications. 【F:src/valanga/represention_for_evaluation.py†L9-L22】【F:src/valanga/representation_factory.py†L7-L55】
- **Progress reporting**: `PlayerProgressMessage` communicates per-player progress percentages during long-running work. 【F:src/valanga/progress_messsage.py†L9-L18】

## Installation
```bash
pip install .
```
The project targets Python 3.13 and has no required runtime dependencies.

## Quick start
Below is a minimal example that marks a finished game and obtains an evaluation structure:
```python
from valanga import ForcedOutcome, OverEvent
from valanga.over_event import HowOver, Winner

# A checkmate where white wins.
over_event = OverEvent(how_over=HowOver.WIN, who_is_winner=Winner.WHITE)

# Record the forced outcome and the line of optimal moves that lead to it.
forced = ForcedOutcome(outcome=over_event, line=["e2e4", "e7e5"])
print(forced.outcome.get_over_tag())  # -> OverTags.TAG_WIN_WHITE
```

To wire in a custom state representation, supply callables to `RepresentationFactory` that know how to build representations from a `State` and its modifications.

## Development
Install the development dependencies and run the test suite:
```bash
pip install -e '.[dev]'
pytest
```
