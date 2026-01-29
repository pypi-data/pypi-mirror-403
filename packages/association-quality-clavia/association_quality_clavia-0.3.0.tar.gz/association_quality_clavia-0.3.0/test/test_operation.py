"""."""

from association_quality_clavia import UPD_ID_LOOSE, AssociationQuality, BinClass


def test_classify_case1234(aq: AssociationQuality) -> None:
    """."""
    assert aq.classify(0, 0, True) == BinClass.TP
    assert aq.num_fn == 0 and aq.num_tp == 1 and aq.num_tn == 0 and aq.num_fp == 0
    assert aq.classify(0, 1, True) == BinClass.FN
    assert aq.num_fn == 1 and aq.num_tp == 1 and aq.num_tn == 0 and aq.num_fp == 0
    assert aq.classify(0, -1, True) == BinClass.FN
    assert aq.num_fn == 2 and aq.num_tp == 1 and aq.num_tn == 0 and aq.num_fp == 0
    assert aq.classify(0, UPD_ID_LOOSE, True) == BinClass.FN
    assert aq.num_fn == 3 and aq.num_tp == 1 and aq.num_tn == 0 and aq.num_fp == 0


def test_classify_case5678(aq: AssociationQuality) -> None:
    """."""
    assert aq.classify(1, 2, False) == BinClass.FP
    assert aq.num_fp == 1 and aq.num_tp == 0 and aq.num_tn == 0 and aq.num_fn == 0
    assert aq.classify(1, -1, False) == BinClass.FP
    assert aq.num_fp == 2 and aq.num_tp == 0 and aq.num_tn == 0 and aq.num_fn == 0
    assert aq.classify(1, UPD_ID_LOOSE, False) == BinClass.TN
    assert aq.num_fp == 2 and aq.num_tp == 0 and aq.num_tn == 1 and aq.num_fn == 0


def test_classify_case9_10_11_12(aq: AssociationQuality) -> None:
    """."""
    assert aq.classify(-1, 1, False) == BinClass.FP
    assert aq.num_fp == 1 and aq.num_tp == 0 and aq.num_tn == 0 and aq.num_fn == 0
    assert aq.classify(-1, -1, False) == BinClass.TN
    assert aq.num_fp == 1 and aq.num_tp == 0 and aq.num_tn == 1 and aq.num_fn == 0
    assert aq.classify(-1, UPD_ID_LOOSE, False) == BinClass.TN
    assert aq.num_fp == 1 and aq.num_tp == 0 and aq.num_tn == 2 and aq.num_fn == 0
