import pytest

from valanga.game import Color
from valanga.over_event import HowOver, OverEvent, OverTags, Winner


@pytest.mark.parametrize(
    "who, expected",
    [
        (Winner.WHITE, OverTags.TAG_WIN_WHITE),
        (Winner.BLACK, OverTags.TAG_WIN_BLACK),
    ],
)
def test_get_over_tag_win_outcomes(who, expected):
    event = OverEvent(how_over=HowOver.WIN, who_is_winner=who)

    assert event.get_over_tag() == expected
    assert event.is_over() is True
    assert event.is_win() is True
    assert event.is_draw() is False


@pytest.mark.parametrize("winner", [Winner.WHITE, Winner.BLACK])
def test_is_winner_matches_color(winner):
    event = OverEvent(how_over=HowOver.WIN, who_is_winner=winner)

    assert event.is_winner(Color.WHITE) is (winner == Winner.WHITE)
    assert event.is_winner(Color.BLACK) is (winner == Winner.BLACK)


@pytest.mark.parametrize(
    "how_over, winner, expected",
    [
        (HowOver.DRAW, Winner.NO_KNOWN_WINNER, OverTags.TAG_DRAW),
        (HowOver.DO_NOT_KNOW_OVER, Winner.NO_KNOWN_WINNER, OverTags.TAG_DO_NOT_KNOW),
    ],
)
def test_get_over_tag_draw_and_unknown(how_over, winner, expected):
    event = OverEvent(how_over=how_over, who_is_winner=winner)

    assert event.get_over_tag() == expected
    assert event.is_over() is (how_over == HowOver.DRAW)
    assert event.is_win() is False
    assert event.is_draw() is (how_over == HowOver.DRAW)


@pytest.mark.parametrize(
    "how_over, who_is_winner",
    [
        (HowOver.WIN, Winner.NO_KNOWN_WINNER),
        (HowOver.DRAW, Winner.WHITE),
    ],
)
def test_post_init_validates_winner_configuration(how_over, who_is_winner):
    with pytest.raises(AssertionError):
        OverEvent(how_over=how_over, who_is_winner=who_is_winner)


@pytest.mark.parametrize("player", [Color.WHITE, Color.BLACK])
def test_is_winner_requires_win(player):
    event = OverEvent(how_over=HowOver.DRAW, who_is_winner=Winner.NO_KNOWN_WINNER)

    assert event.is_winner(player) is False


@pytest.mark.parametrize(
    "how_over, expected_exception",
    [
        (HowOver.WIN, ValueError),
        (None, ValueError),
    ],
)
def test_get_over_tag_invalid_configurations(how_over, expected_exception):
    event = OverEvent(how_over=HowOver.WIN, who_is_winner=Winner.WHITE)
    event.how_over = how_over  # mutate to bypass post-init validation
    event.who_is_winner = Winner.NO_KNOWN_WINNER

    with pytest.raises(expected_exception):
        event.get_over_tag()


@pytest.mark.parametrize(
    "how_over, who_is_winner",
    [
        (HowOver.WIN, Winner.WHITE),
        (HowOver.WIN, Winner.BLACK),
    ],
)
def test_test_method_for_wins(how_over, who_is_winner):
    event = OverEvent(how_over=how_over, who_is_winner=who_is_winner)

    event.test()


def test_test_method_invalid_draw_configuration():
    event = OverEvent(how_over=HowOver.DRAW, who_is_winner=Winner.NO_KNOWN_WINNER)

    with pytest.raises(AssertionError):
        event.test()


def test_bool_raises():
    event = OverEvent()

    with pytest.raises(ValueError):
        bool(event)
