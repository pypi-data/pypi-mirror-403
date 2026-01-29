"""Classification of the tracker output into TP, TN, FP, FN.

Classification is possible due to a suitable instrumentation of the tracker.
Namely, the *annotation* IDs supplied together with measurement vectors are treated
as ground-truth reference. Namely, the real objects have detection IDs greater than or
equal to 0, while clutter detections are marked with negative unity -1. The annotation IDs
are greater than -2. Other values will raise errors in the classifier.

While creating a new track, the tracker stores the *annotation* ID in the new track.
The annotation ID does not change in the lifetime of the track. Apart from the annotation ID,
the instrumented track feature an *update* ID. The update ID is initialized to the
annotation ID at first. However, unlike the annotation ID, the update ID generally changes
in every association procedure. If the association matches a track with a detection, then
the update ID is assigned to the matched detection ID. If the association does not match
a particular track with any detection, then the update ID gets a *loose* value.
By convention, we use -9999 as the loose value.
"""

from enum import Enum
from typing import Dict


UPD_ID_LOOSE = -9999
ANN_ID_ABSENT = -1000


class BinClass(Enum):
    TN = 0
    FN = 1
    FP = 2
    TP = 3


class AssociationQuality(object):
    """Tracks and classifies the quality of associations in a tracker.

    This class maintains counts of true positives (TP), true negatives (TN),
    false positives (FP), and false negatives (FN) based on the association
    between detections and tracks. It provides methods to reset counts,
    retrieve classification ratios, and classify individual associations.
    """

    def __init__(self) -> None:
        """Initialize the AssociationQuality instance with zero counts."""
        self.num_tp = 0  # Count of true positives
        self.num_tn = 0  # Count of true negatives
        self.num_fp = 0  # Count of false positives
        self.num_fn = 0  # Count of false negatives

    def reset(self) -> None:
        """Reset all classification counts to zero."""
        self.num_tp = 0
        self.num_tn = 0
        self.num_fp = 0
        self.num_fn = 0

    def __repr__(self) -> str:
        """Return a string representation of the current classification counts.

        Returns:
            str: A formatted string showing the counts of TP, TN, FP, and FN.
        """
        cc = self
        return f'AssociationQuality(TP {cc.num_tp} TN {cc.num_tn} FP {cc.num_fp} FN {cc.num_fn})'

    def get_confusion_matrix(self) -> Dict[str, int]:
        """Return the dictionary with confusion matrix (keys 'tp', 'fp', 'fn' and 'tp').

        Returns:
            The dictionary representing the confusion matrix.
        """
        return {'tp': self.num_tp, 'tn': self.num_tn, 'fp': self.num_fp, 'fn': self.num_fn}

    def classify(self, ann_id: int, upd_id: int, is_supplied: bool) -> BinClass:
        """Classify and accumulate the results of an association.

        Args:
            ann_id: The annotation ID from the instrumented target.
            upd_id: The update ID from the instrumented target.
            is_supplied: Indicates if the detection with `det_id` was supplied to tracker.

        Raises:
            RuntimeError: an internal error occurs due to invalid ID combinations.

        Returns:
            The BinClass enumerable.
        """
        if ann_id >= 0 and is_supplied:
            if ann_id == upd_id:
                self.num_tp += 1
                return BinClass.TP
            elif upd_id >= 0:
                self.num_fn += 1
                return BinClass.FN
            elif upd_id == -1:
                self.num_fn += 1
                return BinClass.FN
            elif upd_id == UPD_ID_LOOSE:
                self.num_fn += 1
                return BinClass.FN
            else:
                raise RuntimeError('Internal 1', ann_id, upd_id, is_supplied)
        elif ann_id >= 0 and not is_supplied:
            if ann_id == upd_id:
                raise RuntimeError('Internal 2', ann_id, upd_id, is_supplied)
            elif upd_id >= 0:
                self.num_fp += 1
                return BinClass.FP
            elif upd_id == -1:
                self.num_fp += 1
                return BinClass.FP
            elif upd_id == UPD_ID_LOOSE:
                self.num_tn += 1
                return BinClass.TN
            else:
                raise RuntimeError('Internal 3', ann_id, upd_id, is_supplied)
        elif ann_id == -1:
            if ann_id == upd_id:
                self.num_tn += 1
                return BinClass.TN
            elif upd_id >= 0:
                self.num_fp += 1
                return BinClass.FP
            elif upd_id == UPD_ID_LOOSE:
                self.num_tn += 1
                return BinClass.TN
            else:
                raise RuntimeError('Internal 4', ann_id, upd_id, is_supplied)
        else:
            raise RuntimeError('Internal 5', ann_id, upd_id, is_supplied)
