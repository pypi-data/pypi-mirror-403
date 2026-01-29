# Classification via instrumented association in multiple-object trackers

The package provides a classifier machinery working on top of an instrumented
multi-object tracker fed with *identified detections*. An example of *identified detections*
are *annotations* in the simplest case.

The acronym ClavIA stands for classification via instrumented association.

## Installation

Should be as easy as `pip install association-quality-clavia`, but if you downloaded the repo,
then `uv sync` standing in the root folder.

## Usage

The instrumentation consists in adding an *annotation* and *update IDs* to the target objects
(tracks) processed in the tracker. The annotation ID is initialized at the target creation time.
The update ID is updated after each association procedure.

The classifier procedure (method `AssociationQuality.classify`) should be called after each
tracking step. It is capable of telling apart true positives (TP), false positives (FP),
false negatives (FN) and true negatives (TN) *if provided with* the annotation and update IDs
and a *supply flag* calculated at the current step. The supply flag is easy to get
as `ann_id in annotation_ids`.

The method `AssociationQuality.classify` returns the object of type `BinClass`.
The class `BinClass` enumerates `TN`, `FN`, `FP`, `TP`.

The use of the module will be demonstrated in the packages (repos) `pure-ab-3d-mot` and
`eval-ab-3d-mot`. The package `pure-ab-3d-mot` features a refactored AB3DMOT tracker
instrumented according to the needs of the binary classification of the association.
The package `eval-ab-3d-mot` features the evaluation part extracted from the original
AB3DMOT as well as the code to use the association classifier from this package.
