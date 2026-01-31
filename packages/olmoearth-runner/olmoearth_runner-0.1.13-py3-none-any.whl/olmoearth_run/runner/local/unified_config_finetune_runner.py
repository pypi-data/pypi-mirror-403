import logging
import shutil
import uuid
from pathlib import Path
from os import PathLike

from olmoearth_run.runner.steps.prepare_labeled_windows_step_definition import (
    PrepareLabeledWindowsStepDefinition,
)
from olmoearth_run.shared.models.model_stage_paths import (
    ANNOTATION_FEATURES_FILE_NAME,
    ANNOTATION_TASK_FEATURES_FILE_NAME,
)
from olmoearth_run.shared.models.fine_tuning_scratch_space import (
    FineTuningScratchSpace,
    OLMOEARTH_CONFIG_FILE_NAME,
)
from olmoearth_run.shared.models.api.task_args import (
    PrepareLabeledWindowsTaskArgs,
    DatasetBuildFromWindowsTaskArgs,
    FineTuneTaskArgs,
)
from olmoearth_run.shared.models.api.task_results import (
    PrepareLabeledWindowsTaskResults,
    DatasetBuildFromWindowsTaskResults,
    FineTuneTaskResults,
)
from olmoearth_run.runner.steps.dataset_build_from_windows_step_definition import (
    DatasetBuildFromWindowsStepDefinition,
)
from olmoearth_run.runner.steps.fine_tuning_step_definition import (
    FineTuningStepDefinition,
)


logger = logging.getLogger(__name__)


class UnifiedConfigFineTuneRunner:
    """
    Local runner for the OlmoEarth fine-tuning pipeline.

    Uses the unified OlmoEarthConfig format (olmoearth_config.yaml) for configuration.
    """

    def __init__(
        self,
        project_path: PathLike,
        scratch_path: PathLike,
    ):
        self.project_path = Path(project_path)
        self.scratch_path = Path(scratch_path)
        self.scratch_space = FineTuningScratchSpace(root_path=str(self.scratch_path))
        self.model_stage_paths = self.scratch_space.model_stage_paths
        self.dataset_path = Path(self.model_stage_paths.default_dataset_path)
        self.step_id = uuid.uuid4()

        self._setup_project_env()

    def _setup_project_env(self) -> None:
        """Set up the project environment in the scratch space by copying config and creating symlinks."""

        self.dataset_path.mkdir(parents=True, exist_ok=True)

        # Copy olmoearth_config.yaml to scratch space
        olmoearth_config_path = self.project_path / OLMOEARTH_CONFIG_FILE_NAME
        if not olmoearth_config_path.exists():
            raise FileNotFoundError(
                f"Required project file not found: {olmoearth_config_path}. "
                + "Expected unified OlmoEarthConfig format (olmoearth_config.yaml)."
            )

        scratch_config_path = Path(self.scratch_space.olmoearth_config_path)
        scratch_config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(olmoearth_config_path, scratch_config_path)

        # Create dataset directory
        Path(self.model_stage_paths.default_dataset_path).parent.mkdir(
            parents=True, exist_ok=True
        )

        # Symlink annotation feature files (still required for labeled data prep)
        annotation_files: list[tuple[Path, Path]] = [
            (
                self.project_path / ANNOTATION_FEATURES_FILE_NAME,
                Path(self.model_stage_paths.annotation_features_path),
            ),
            (
                self.project_path / ANNOTATION_TASK_FEATURES_FILE_NAME,
                Path(self.model_stage_paths.annotation_task_features_path),
            ),
        ]

        for target, link in annotation_files:
            if not target.exists():
                raise FileNotFoundError(f"Required project file not found: {target}")

            if not link.exists():
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)

    def prepare_labeled_windows(self) -> PrepareLabeledWindowsTaskResults:
        logger.info("Preparing labeled windows")
        task_args = PrepareLabeledWindowsTaskArgs(
            dataset_path=str(self.dataset_path),
            scratch_path=str(self.scratch_path),
        )
        return PrepareLabeledWindowsStepDefinition().run(task_args)

    def build_dataset_from_windows(self) -> DatasetBuildFromWindowsTaskResults:
        logger.info("Building dataset from windows")
        task_args = DatasetBuildFromWindowsTaskArgs(
            dataset_path=str(self.dataset_path),
            olmoearth_config_path=self.scratch_space.olmoearth_config_path,
        )
        return DatasetBuildFromWindowsStepDefinition().run(task_args)

    def fine_tune(self) -> FineTuneTaskResults:
        logger.info("Fine tuning")
        task_args = FineTuneTaskArgs(
            dataset_path=str(self.dataset_path),
            scratch_path=str(self.scratch_path),
            step_id=self.step_id,
        )
        return FineTuningStepDefinition().run(task_args)

    def run_pipeline(self) -> None:
        logger.info("Running full fine tune pipeline")
        self.prepare_labeled_windows()
        self.build_dataset_from_windows()
        self.fine_tune()
