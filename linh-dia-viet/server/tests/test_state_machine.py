import itertools

import pytest

from app.state_machine import (MAIN_LINE, TRANSITIONS, InvalidTransition, OrderStatus as S, can_transition,
                               check_transition, path_forward)

VALID = {
    (S.CREATED, S.AWAITING_PAYMENT), (S.CREATED, S.CANCELLED),
    (S.AWAITING_PAYMENT, S.PAID), (S.AWAITING_PAYMENT, S.CANCELLED),
    (S.PAID, S.SCHEDULED), (S.PAID, S.CANCELLED), (S.PAID, S.REJECTED),
    (S.SCHEDULED, S.DELIVERED), (S.SCHEDULED, S.CANCELLED), (S.SCHEDULED, S.REJECTED), (S.SCHEDULED, S.FAILED),
    (S.DELIVERED, S.PLAYING), (S.DELIVERED, S.FAILED),
    (S.PLAYING, S.PLAYED), (S.PLAYING, S.FAILED),
    (S.PLAYED, S.EVIDENCE_RECEIVED), (S.PLAYED, S.COMPLETED),
    (S.EVIDENCE_RECEIVED, S.COMPLETED),
    (S.REJECTED, S.REFUND_REQUESTED),
    (S.FAILED, S.SCHEDULED), (S.FAILED, S.REFUND_REQUESTED),
    (S.CANCELLED, S.REFUND_REQUESTED),
    (S.REFUND_REQUESTED, S.REFUNDED),
}
ALL_PAIRS = list(itertools.product(S, S))


def test_table_matches_spec():
    assert {(a, b) for a, nxt in TRANSITIONS.items() for b in nxt} == VALID
    assert set(TRANSITIONS) == set(S)


@pytest.mark.parametrize("src,dst", sorted(VALID))
def test_valid(src, dst):
    assert can_transition(src, dst)
    check_transition(src, dst)


@pytest.mark.parametrize("src,dst", [p for p in ALL_PAIRS if p not in VALID])
def test_invalid(src, dst):
    assert not can_transition(src, dst)
    with pytest.raises(InvalidTransition):
        check_transition(src, dst)


def test_main_line_is_walkable():
    for a, b in zip(MAIN_LINE, MAIN_LINE[1:]):
        assert can_transition(a, b)


def test_terminal_states():
    assert TRANSITIONS[S.COMPLETED] == set() and TRANSITIONS[S.REFUNDED] == set()


def test_path_forward():
    assert path_forward("delivered", "played") == [S.PLAYING, S.PLAYED]
    assert path_forward("played", "delivered") == []
    assert path_forward("failed", "played") == []
