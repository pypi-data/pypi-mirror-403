import json
from collections.abc import Sequence
from typing import Any

from lightning.pytorch import LightningModule, Trainer
from lightning.pytorch.callbacks import BasePredictionWriter
from upath import UPath

from rslearn.train.model_context import ModelOutput


class EvaluationMetadataWriter(BasePredictionWriter):
    """Saves metadata during model evaluation.

    This callback captures the patch_bounds from each prediction batch
    and saves them to a JSON file. This allows us to later read predictions
    and labels at the exact locations used during inference for metric calculation.
    """

    def __init__(self, output_path: UPath):
        super().__init__(write_interval="batch")
        self.output_path = output_path
        self.metadata: dict[str, dict[str, Any]] = {}

    def write_on_batch_end(
        self,
        trainer: Trainer,
        pl_module: LightningModule,
        prediction: ModelOutput,
        batch_indices: Sequence[int] | None,
        batch: tuple[list, list, list],
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Save metadata for each window in the batch."""
        _, _, metadatas = batch
        for metadata in metadatas:
            self.metadata[metadata.window_name] = {
                "patch_bounds": list(metadata.patch_bounds),
                "window_bounds": list(metadata.window_bounds),
                "window_group": metadata.window_group,
            }

    def on_predict_end(self, trainer: Trainer, pl_module: LightningModule) -> None:
        self.output_path.write_text(json.dumps(self.metadata, indent=2))
