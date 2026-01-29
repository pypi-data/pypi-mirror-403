import pytest

from web_sdk.utils.statements import first, not_none


def test_not_none():
    assert not_none(None) is None
    assert not_none(None, default=1) == 1
    assert not_none(None, 0, default=1) == 0
    assert not_none(0, 1, default=2) == 0


def test_first():
    assert first([]) is None
    assert first([0, 1]) == 0
    assert first([], default=0) == 0

    with pytest.raises(StopIteration):
        first([], raise_exception=True)

    assert first([], default=0, raise_exception=True) == 0
    assert first([], default=None, raise_exception=True) is None

    assert first([1, 2], lambda x: x > 1) == 2
    assert first([1, 2], lambda x: x > 2) is None

    with pytest.raises(StopIteration):
        first([1, 2], lambda x: x > 2, raise_exception=True)

    assert first([1, 2], lambda x: x > 2, default=3, raise_exception=True) == 3
    assert first([1, 2], lambda x: x > 2, default=None, raise_exception=True) is None
