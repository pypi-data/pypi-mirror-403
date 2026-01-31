"""
Example script to run the fine-tuning pipeline locally.
"""

import logging
import shutil
from pathlib import Path

from olmoearth_run.runner.local.unified_config_finetune_runner import (
    UnifiedConfigFineTuneRunner,
)
from olmoearth_shared.tools.telemetry.logging_tools import configure_logging

configure_logging()
logger = logging.getLogger("olmoearth_run.runner.local.unified_config_example.finetune")


def main() -> None:
    logger.info("Task: Binary segmentation of labeled polygons")

    example_dir = Path(__file__).parent
    project_path = example_dir / "project"
    scratch_path = example_dir / "scratch"
    output_path = example_dir / "output"

    # Ensure directories exist
    scratch_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)

    runner = UnifiedConfigFineTuneRunner(
        project_path=project_path,
        scratch_path=scratch_path,
    )
    logger.info("Runner initialized successfully")

    logger.info("STEP 1/3: Preparing labeled windows")
    runner.prepare_labeled_windows()

    logger.info("STEP 2/3: Building dataset from windows")
    runner.build_dataset_from_windows()

    logger.info("STEP 3/3: Fine-tuning model")
    result = runner.fine_tune()

    # Copy checkpoint to output directory
    checkpoint_src = Path(result.checkpoint_path)
    checkpoint_dst = output_path / "model.ckpt"
    shutil.copy2(checkpoint_src, checkpoint_dst)
    logger.info(f"Checkpoint saved to: {checkpoint_dst}")

    logger.info(f"Fine-tuned model: {checkpoint_dst}")


if __name__ == "__main__":
    main()
