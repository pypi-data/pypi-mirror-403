from collections import Counter

from valanga.representation_factory import RepresentationFactory


class DummyRepresentation:
    pass


def test_create_from_transition_root_uses_full_creator():
    calls = Counter()

    def create_from_state(state):
        calls["create_from_state"] += 1
        return ("state", state)

    factory = RepresentationFactory(
        create_from_state=create_from_state, create_from_state_and_modifications=None
    )

    result = factory.create_from_transition(
        state="root", previous_state_representation=None, modifications=None
    )

    assert result == ("state", "root")
    assert calls["create_from_state"] == 1


def test_create_from_transition_no_modifications_falls_back_to_state():
    calls = Counter()

    def create_from_state(state):
        calls["create_from_state"] += 1
        return ("state", state)

    factory = RepresentationFactory(
        create_from_state=create_from_state, create_from_state_and_modifications=None
    )

    result = factory.create_from_transition(
        state="child",
        previous_state_representation=DummyRepresentation(),
        modifications=None,
    )

    assert result == ("state", "child")
    assert calls["create_from_state"] == 1


def test_create_from_transition_with_modifications():
    calls = Counter()

    def create_from_state_and_modifications(
        state, state_modifications, previous_state_representation
    ):
        calls["create_from_state_and_modifications"] += 1
        return (state, state_modifications, previous_state_representation)

    factory = RepresentationFactory(
        create_from_state=lambda state: ("unused", state),
        create_from_state_and_modifications=create_from_state_and_modifications,
    )

    previous = DummyRepresentation()
    result = factory.create_from_transition(
        state="child", previous_state_representation=previous, modifications="delta"
    )

    assert result == ("child", "delta", previous)
    assert calls["create_from_state_and_modifications"] == 1
