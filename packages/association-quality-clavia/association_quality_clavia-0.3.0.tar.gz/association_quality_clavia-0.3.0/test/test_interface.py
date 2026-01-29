"""."""

import pytest

from association_quality_clavia import AssociationQuality


@pytest.fixture
def aq1234(aq: AssociationQuality) -> AssociationQuality:
    """."""
    aq.num_tp = 1
    aq.num_tn = 2
    aq.num_fp = 3
    aq.num_fn = 4
    return aq


def test_get_confusion_matrix(aq1234: AssociationQuality) -> None:
    """."""
    cm = aq1234.get_confusion_matrix()
    assert len(cm) == 4
    assert cm['tp'] == 1
    assert cm['tn'] == 2
    assert cm['fp'] == 3
    assert cm['fn'] == 4


def test_repr(aq1234: AssociationQuality) -> None:
    """."""
    assert repr(aq1234) == 'AssociationQuality(TP 1 TN 2 FP 3 FN 4)'


def test_reset(aq1234: AssociationQuality) -> None:
    """."""
    aq1234.reset()
    assert repr(aq1234) == 'AssociationQuality(TP 0 TN 0 FP 0 FN 0)'
