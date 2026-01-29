"""."""

import pytest

from association_quality_clavia import AssociationQuality


def test_exception_1(aq: AssociationQuality) -> None:
    """."""
    with pytest.raises(RuntimeError) as err:
        aq.classify(0, -2, True)
    assert err.value.args == ('Internal 1', 0, -2, True)

    with pytest.raises(RuntimeError) as err:
        aq.classify(1, -2, True)
    assert err.value.args == ('Internal 1', 1, -2, True)


def test_exception_2(aq: AssociationQuality) -> None:
    """."""
    with pytest.raises(RuntimeError) as err:
        aq.classify(1, 1, False)
    assert err.value.args == ('Internal 2', 1, 1, False)


def test_exception_3(aq: AssociationQuality) -> None:
    """."""
    with pytest.raises(RuntimeError) as err:
        aq.classify(2, -567, False)

    assert err.value.args == ('Internal 3', 2, -567, False)


def test_exception_4(aq: AssociationQuality) -> None:
    """."""
    with pytest.raises(RuntimeError) as err:
        aq.classify(-1, -2, False)
    assert err.value.args == ('Internal 4', -1, -2, False)


def test_exception_5(aq: AssociationQuality) -> None:
    """."""
    with pytest.raises(RuntimeError) as err:
        aq.classify(-2, 0, False)

    assert err.value.args == ('Internal 5', -2, 0, False)
