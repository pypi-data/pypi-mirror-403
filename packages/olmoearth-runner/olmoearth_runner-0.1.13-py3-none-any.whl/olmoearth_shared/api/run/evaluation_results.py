"""
Evaluation results data models.

Storage strategy:
- GCS (granular files):
{model_stage_id}/evaluation/
├── confusion_matrix.json
└── confusion_matrix_examples/
    ├── predicted_0_actual_0.json
    ├── predicted_0_actual_1.json
    ├── predicted_1_actual_0.json
    └── ...
"""

import uuid
from typing import Literal

from geojson_pydantic.geometries import Geometry
from pydantic import BaseModel, Field


class CellExample(BaseModel):
    """
    Window-level provenance data for a confusion matrix cell.

    Tracks which annotation task and window contributed pixels to a specific cell.
    Users can use the source_task_id to look up the full annotation task in studio.
    """

    window_id: str = Field(description="Identifies the rslearn window")
    source_task_id: uuid.UUID = Field(description="The annotation task that created this window")
    window_geometry: Geometry = Field(description="GeoJSON geometry of the window bounds. Used in studio if a task has more than one annotation")
    pixel_count: int = Field(description="How many pixels from this window fell into this cell")


class ConfusionMatrixCellExamples(BaseModel):
    """
    Contains list of provenance data for a specific confusion matrix cell.

    Stored separately in GCS at: confusion_matrix_examples/predicted_{X}_actual_{Y}.json
    Loaded on-demand when user clicks a cell in the UI.
    """

    predicted_class_id: str
    actual_class_id: str
    total_count: int = Field(description="Total number of windows contributing to this cell")
    examples: list[CellExample] = Field(description="All windows/tasks that contributed to this cell")


class PerClassMetrics(BaseModel):
    """Accuracy metrics for a single class."""

    class_name: str = Field(description="Name of the class")
    precision: float = Field(description="Precision: TP / (TP + FP) - when model predicts this class, how often is it correct?", ge=0.0, le=1.0)
    recall: float = Field(description="Recall: TP / (TP + FN) - of all actual instances of this class, how many did we find?", ge=0.0, le=1.0)
    f1_score: float = Field(description="F1 score: harmonic mean of precision and recall", ge=0.0, le=1.0)
    ground_truth_pixel_count: int = Field(description="Number of ground truth pixels for this class", ge=0)


class ConfusionMatrixMetric(BaseModel):
    """
    Complete confusion matrix evaluation results.

    Contains the full NxN matrix, per-class metrics (precision/recall/F1), and cell-level data
    with provenance information linking predictions back to annotation tasks.
    This is stored in GCS as confusion_matrix.json and referenced from the DB.
    """

    metric_type: Literal["confusion_matrix"] = Field(default="confusion_matrix")
    class_names: list[str] = Field(description="Ordered list of class names corresponding to matrix indices")
    matrix: list[list[int]] = Field(description="NxN matrix where matrix[i][j] = pixels predicted as class i but actually class j")
    total_pixels: int = Field(description="Total number of pixels evaluated")
    overall_accuracy: float = Field(description="Overall accuracy: correct predictions / total pixels", ge=0.0, le=1.0)
    mean_f1_score: float = Field(description="Macro-averaged F1 score across all classes", ge=0.0, le=1.0)
    per_class_metrics: list[PerClassMetrics] = Field(description="Detailed metrics (precision, recall, F1) for each class")


# Type definitions for validation by prediction type
# Segmentation = per-pixel classification (semantic segmentation)
SegmentationMetricType = Literal["confusion_matrix"]

# TODO: Add other prediction types as they're implemented
# PerPixelRegressionMetricType = Literal["mae", "rmse"]
# WindowRegressionMetricType = Literal["mae", "rmse", "r_squared"]
# WindowClassificationMetricType = Literal["precision_recall_curve", "roc_auc", "accuracy"]
# DetectionMetricType = Literal["mean_average_precision", "iou"]

EvaluationMetricType = SegmentationMetricType  # Union with others when added

# Runtime configuration - available metrics by prediction type
# Maps prediction type names to their available metric types
SEGMENTATION_METRICS = ["confusion_matrix"]
# PER_PIXEL_REGRESSION_METRICS = ["mae", "rmse"]  # TODO
# WINDOW_REGRESSION_METRICS = ["mae", "rmse", "r_squared"]  # TODO
# WINDOW_CLASSIFICATION_METRICS = ["precision_recall_curve", "roc_auc", "accuracy"]  # TODO
# DETECTION_METRICS = ["mean_average_precision", "iou"]  # TODO

DEFAULT_METRICS_BY_PREDICTION_TYPE = {
    "segmentation": SEGMENTATION_METRICS,
    # "per_pixel_regression": PER_PIXEL_REGRESSION_METRICS,  # TODO
    # "window_regression": WINDOW_REGRESSION_METRICS,  # TODO
    # "window_classification": WINDOW_CLASSIFICATION_METRICS,  # TODO
    # "detection": DETECTION_METRICS,  # TODO
}


def get_default_metrics_for_task(task_type: str) -> list[str]:
    """
    Returns default evaluation metrics for a given prediction type.

    Args:
        task_type: Prediction type (e.g., "segmentation", "per_pixel_regression", "window_classification")

    Returns:
        List of default metric type strings for this prediction type
    """
    return DEFAULT_METRICS_BY_PREDICTION_TYPE.get(task_type.lower(), [])
