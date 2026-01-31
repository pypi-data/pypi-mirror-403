"""
Local runner for the OlmoEarth prediction pipeline using unified config.

This runner uses the unified OlmoEarthConfig format (olmoearth_config.yaml) for configuration.
The step definitions automatically detect unified config and use PredictionToolsClassLoader
to instantiate partitioners and postprocessors.
"""

import logging
import shutil
import sys
import uuid
from os import PathLike
from pathlib import Path

from olmoearth_run.runner.steps.combine_partitions_step_definition import (
    CombinePartitionsStepDefinition,
)
from olmoearth_run.runner.steps.create_partitions_step_definition import (
    CreatePartitionsStepDefinition,
)
from olmoearth_run.runner.steps.dataset_build_step_definition import (
    DatasetBuildStepDefinition,
)
from olmoearth_run.runner.steps.postprocess_partition_step_definition import (
    PostprocessPartitionStepDefinition,
)
from olmoearth_run.runner.steps.run_inference_step_definition import (
    RunInferenceStepDefinition,
)
from olmoearth_run.shared.models.api.task_args import (
    CombinePartitionsTaskArgs,
    CreatePartitionsTaskArgs,
    DatasetBuildTaskArgs,
    PostprocessPartitionTaskArgs,
    RunInferenceTaskArgs,
)
from olmoearth_run.shared.models.api.task_results import (
    CombinePartitionsTaskResults,
    DatasetBuildTaskResults,
    InferenceResultsDataType,
    PostprocessPartitionTaskResults,
    RunInferenceTaskResults,
)
from olmoearth_run.shared.models.model_stage_paths import (
    CHECKPOINT_FILE_NAME,
    ModelStagePaths,
)
from olmoearth_run.shared.models.prediction_scratch_space import (
    OLMOEARTH_CONFIG_FILE_NAME,
    PREDICTION_REQUEST_GEOMETRY_FILE_NAME,
    PredictionScratchSpace,
)

logger = logging.getLogger(__name__)

NAMESPACE_UNIFIED_PREDICT_RUNNER = uuid.UUID("0f94b556-2bc6-40c2-a8ae-e36d4ab0cf03")


class UnifiedConfigPredictRunner:
    """
    Local runner for the OlmoEarth prediction pipeline.

    Uses the unified OlmoEarthConfig format (olmoearth_config.yaml) for configuration.
    """

    def __init__(
        self,
        project_path: PathLike,
        scratch_path: PathLike,
        request_geometry_path: PathLike | None = None,
        checkpoint_path: PathLike | None = None,
    ):
        self.project_path = Path(project_path)
        self.scratch_path = Path(scratch_path)
        self.dataset_path = f"{self.scratch_path}/dataset_0"

        self.stage_name = "model_stage_0"
        self.stage_path = self.scratch_path / self.stage_name
        self.project_name = self.project_path.name
        self.inference_results_data_type: InferenceResultsDataType | None = None

        self.scratch = PredictionScratchSpace(root_path=str(self.scratch_path))
        self.model_stage_paths = ModelStagePaths(root_path=str(self.stage_path))

        self.project_uuid_namespace = uuid.uuid5(
            NAMESPACE_UNIFIED_PREDICT_RUNNER, self.project_name
        )
        self.model_stage_id = uuid.uuid5(self.project_uuid_namespace, self.stage_name)

        self.checkpoint_path = Path(
            checkpoint_path or self.project_path / CHECKPOINT_FILE_NAME
        )
        self.request_geometry_path = Path(
            request_geometry_path
            or self.project_path / PREDICTION_REQUEST_GEOMETRY_FILE_NAME
        )

        logger.info(f"Project Path: {self.project_path}")
        logger.info(f"Scratch Path: {self.scratch_path}")
        logger.info(f"Dataset Path: {self.dataset_path}")

        self._setup_project_env()

    def _setup_project_env(self) -> None:
        """Set up the project environment in the scratch space by copying config and creating symlinks."""
        Path(self.scratch_path).mkdir(parents=True, exist_ok=True)
        Path(self.dataset_path).mkdir(exist_ok=True)

        # Copy olmoearth_config.yaml to scratch space
        # Step definitions detect this file and use unified config automatically
        olmoearth_config_path = self.project_path / OLMOEARTH_CONFIG_FILE_NAME
        if not olmoearth_config_path.exists():
            logger.error(
                f"Required project file not found: {olmoearth_config_path}. "
                "Expected unified OlmoEarthConfig format (olmoearth_config.yaml)."
            )
            sys.exit(1)

        scratch_config_path = Path(self.scratch.olmoearth_config_path)
        if not scratch_config_path.exists():
            logger.info(f"Copying {olmoearth_config_path} to {scratch_config_path}")
            scratch_config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(olmoearth_config_path, scratch_config_path)
        else:
            logger.info(f"{scratch_config_path} already exists. Skipping copy.")

        # Set up symlinks for checkpoint and request geometry
        symlink_files: list[tuple[Path, Path, bool]] = [
            # (target, link, is_optional)
            (
                self.request_geometry_path,
                Path(self.scratch.prediction_request_geometry_path),
                False,
            ),
            (self.checkpoint_path, Path(self.model_stage_paths.checkpoint_path), True),
        ]

        for target, link, is_optional in symlink_files:
            if not link.exists():
                if not target.exists():
                    if is_optional:
                        logger.warning(
                            f"Optional file {target} does not exist. Skipping linking."
                        )
                        continue
                    else:
                        logger.error(f"Required project file {target} does not exist.")
                        sys.exit(1)
                logger.info(f"{link} does not exist yet. Linking {target} to {link}")
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)
            else:
                logger.info(
                    f"{link} already exists. Skipping linking {target} to {link}"
                )

    def partition(self) -> list[str]:
        """Partition the original request feature into smaller features for processing"""
        partition_args = CreatePartitionsTaskArgs(
            scratch_path=str(self.scratch_path),
            model_stage_root_path=self.model_stage_paths.root_path,
            model_stage_id=self.model_stage_id,
            dataset_path=self.dataset_path,
        )
        return CreatePartitionsStepDefinition().run(partition_args).partition_ids

    def build_dataset(self, partition_ids: list[str]) -> list[DatasetBuildTaskResults]:
        """Further partition the dataset into windows and build the rslearn dataset for the given partition"""
        logger.info(f"Building dataset for {len(partition_ids)} partitions")
        results: list[DatasetBuildTaskResults] = []
        for partition_id in partition_ids:
            dataset_build_args = DatasetBuildTaskArgs(
                partition_ids=[partition_id],
                scratch_path=str(self.scratch_path),
                model_stage_id=self.model_stage_id,
                model_stage_root_path=self.model_stage_paths.root_path,
                dataset_path=self.dataset_path,
            )
            results.append(DatasetBuildStepDefinition().run(dataset_build_args))
        return results

    def run_inference(self, partition_id: str) -> RunInferenceTaskResults:
        """Run inference on the given partition"""
        logger.debug(f"Running inference step for partition {partition_id}")
        inference_args = RunInferenceTaskArgs(
            partition_ids=[partition_id],
            scratch_path=str(self.scratch_path),
            model_stage_id=self.model_stage_id,
            model_stage_root_path=self.model_stage_paths.root_path,
            dataset_path=self.dataset_path,
        )
        results = RunInferenceStepDefinition().run(inference_args)
        self.inference_results_data_type = results.inference_results_data_type

        return results

    def postprocess(self, partition_id: str) -> PostprocessPartitionTaskResults:
        """Postprocess the results of inference for the given partition"""
        if self.inference_results_data_type is None:
            raise ValueError(
                "inference_results_data_type must be set before postprocessing"
            )

        postprocess_args = PostprocessPartitionTaskArgs(
            partition_ids=[partition_id],
            scratch_path=str(self.scratch_path),
            model_stage_id=self.model_stage_id,
            model_stage_root_path=self.model_stage_paths.root_path,
            dataset_path=self.dataset_path,
        )
        return PostprocessPartitionStepDefinition().run(postprocess_args)

    def combine(self, partition_ids: list[str]) -> CombinePartitionsTaskResults:
        """Combine the results of inference from all partitions into a single result set"""
        if self.inference_results_data_type is None:
            raise ValueError("inference_results_data_type must be set before combining")

        combine_args = CombinePartitionsTaskArgs(
            partition_ids=partition_ids,
            scratch_path=str(self.scratch_path),
            model_stage_id=self.model_stage_id,
            model_stage_root_path=self.model_stage_paths.root_path,
            dataset_path=self.dataset_path,
        )
        return CombinePartitionsStepDefinition().run(combine_args)

    def run_pipeline(
        self, steps: list[str], partitions: list[str] | None = None
    ) -> None:
        """Run the pipeline using the provided steps and partitions."""
        if "partition" in steps:
            logger.info("Running partition step")
            if partitions:
                logger.warning(
                    "Partitions were provided, but the partition step will re-create them anyway."
                )
            partitions = self.partition()
            logger.info(f"Created {len(partitions)} partitions")
        else:
            logger.info("Fetching existing partitions")
            partitions = partitions or self.scratch.get_partitions()
            logger.info(f"Found {len(partitions)} partitions")

        if not partitions:
            logger.error(
                "No partitions found to process. You may have forgotten to: "
                "  - Previously run the `partition` step, "
                "  - Pass `partition` as a step"
                "  - Pass the partition-ids argument."
            )
            sys.exit(1)

        for step in steps:
            if step == "dataset_build":
                logger.info(
                    f"Running dataset build step for {len(partitions)} partitions"
                )
                all(self.build_dataset(partitions))
                logger.info("Completed dataset build step")
            elif step == "inference":
                for partition_id in partitions:
                    self.run_inference(partition_id)
            elif step == "postprocess":
                for partition_id in partitions:
                    self.postprocess(partition_id)

        if "combine" in steps:
            logger.info(f"Running combine step for {len(partitions)} partitions")
            self.combine(partitions)


def main() -> None:
    import argparse

    from olmoearth_shared.tools.telemetry.logging_tools import configure_logging

    parser = argparse.ArgumentParser(
        description="OlmoEarth Unified Config Prediction Runner"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=str(Path.cwd()),
        type=Path,
        help="Path to project directory containing olmoearth_config.yaml",
    )
    parser.add_argument(
        "--scratch-path",
        help="Scratch directory path (default: {project_path}/scratches/{geometry_name})",
    )
    parser.add_argument(
        "--request-geometry-path",
        type=Path,
        help="Path to the input prediction_request_geometry.geojson file",
        default=Path(PREDICTION_REQUEST_GEOMETRY_FILE_NAME),
    )
    parser.add_argument(
        "--checkpoint-path", type=Path, help="Path to the model checkpoint file"
    )
    parser.add_argument(
        "--steps", help="Comma-separated steps to run (default: all steps)"
    )
    parser.add_argument(
        "--partition-ids", help="Comma-separated partition IDs to run steps on"
    )

    args = parser.parse_args()

    configure_logging()

    project_path = Path(args.project_path).absolute()
    # If request geometry path is just a filename, look for it in the project directory
    if args.request_geometry_path.parent == Path("."):
        request_geometry_path = (project_path / args.request_geometry_path).absolute()
    else:
        request_geometry_path = Path(args.request_geometry_path).absolute()
    scratch_path = (
        Path(args.scratch_path).absolute()
        if args.scratch_path
        else project_path / "scratches" / request_geometry_path.stem
    )
    scratch_path.mkdir(parents=True, exist_ok=True)
    checkpoint_path = (
        Path(args.checkpoint_path).absolute() if args.checkpoint_path else None
    )

    runner = UnifiedConfigPredictRunner(
        project_path=project_path,
        scratch_path=scratch_path,
        request_geometry_path=request_geometry_path,
        checkpoint_path=checkpoint_path,
    )

    allowed_steps = [
        "partition",
        "dataset_build",
        "inference",
        "postprocess",
        "combine",
    ]
    steps = args.steps.split(",") if args.steps else allowed_steps
    if len(set(steps).difference(allowed_steps)) > 0:
        logger.error(
            f"Invalid steps provided. Allowed steps are: {', '.join(allowed_steps)}"
        )
        sys.exit(1)

    partition_ids = args.partition_ids.split(",") if args.partition_ids else None
    logger.info(f"Running steps ({','.join(steps)}) on partitions: {partition_ids}")
    runner.run_pipeline(steps, partition_ids)


if __name__ == "__main__":
    main()
