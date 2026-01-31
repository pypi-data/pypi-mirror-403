import json
import logging

from rslearn.arg_parser import RslearnArgumentParser
from rslearn.lightning_cli import RslearnLightningCLI
from rslearn.train.data_module import RslearnDataModule
from rslearn.train.lightning_module import RslearnLightningModule
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.models.operational_context import ModelOperationalContext
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.olmoearth_config.loaders.config import ConfigClassLoader
from olmoearth_run.runner.tools.olmoearth_config.transpilers.olmoearth_to_rslearn import transpile_and_write_model_config
from olmoearth_run.runner.tools.olmoearth_config.utils import ConfigUtils
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_run.shared.models.prediction_scratch_space import (
    PredictionScratchSpace,
    LEGACY_WINDOW_OUTPUT_LAYER_NAME,
)
from olmoearth_run.shared.models.rslearn_template_vars import RslearnTemplateVars
from olmoearth_run.shared.models.api.task_args import RunInferenceTaskArgs
from olmoearth_run.shared.models.api.task_results import (
    RunInferenceTaskResults,
)


logger = logging.getLogger(__name__)


class RunInferenceStepDefinition(BaseStepDefinition[RunInferenceTaskArgs, RunInferenceTaskResults]):
    def run(self, task_args: RunInferenceTaskArgs) -> RunInferenceTaskResults:
        model_stage_paths = ModelStagePaths(root_path=task_args.model_stage_root_path)
        dataset_path = UPath(task_args.dataset_path)
        scratch = PredictionScratchSpace(root_path=task_args.scratch_path)

        # Check if unified config exists - determines which code path to use
        olmoearth_config_path = UPath(scratch.olmoearth_config_path)
        if olmoearth_config_path.exists():
            return self._run_with_unified_config(task_args, scratch, dataset_path, model_stage_paths)
        else:
            return self._run_with_legacy_config(task_args, scratch, dataset_path, model_stage_paths)

    def _run_with_unified_config(
        self,
        task_args: RunInferenceTaskArgs,
        scratch: PredictionScratchSpace,
        dataset_path: UPath,
        model_stage_paths: ModelStagePaths,
    ) -> RunInferenceTaskResults:
        """Run inference using unified OlmoEarthConfig with JIT transpilation per partition."""
        logger.info(f"Using unified config path: {scratch.olmoearth_config_path}")
        olmoearth_config = ConfigClassLoader.load_olmoearth_config(scratch.olmoearth_config_path)

        for partition_id in task_args.partition_ids:
            logger.info(f"Running inference step for partition {partition_id}")
            rslearn_groups = [scratch.get_group(partition_id)]

            # Build ops context with partition-specific groups
            ops_context = ModelOperationalContext(
                step_type=StepType.RUN_INFERENCE,
                dataset_path=str(dataset_path),
                num_data_worker_processes=OlmoEarthSettings.NUM_WORKERS,
                predict_groups=rslearn_groups,
                model_stage_paths=model_stage_paths,
            )

            # JIT transpile to partition-specific path
            model_config_path = UPath(scratch.get_partition_model_config_path(partition_id))
            transpile_and_write_model_config(olmoearth_config, ops_context, model_config_path)

            predict_args = [
                "predict",
                "--config", str(model_config_path),
                "--ckpt_path", model_stage_paths.checkpoint_path,
            ]
            logger.info(f"Running inference on groups {rslearn_groups} with args: {predict_args}")
            self._run_inference_for_groups(predict_args)

        # Determine data type from unified config output schema
        data_type = ConfigUtils.get_output_data_type(olmoearth_config)
        return RunInferenceTaskResults(inference_results_data_type=data_type)

    def _run_with_legacy_config(
        self,
        task_args: RunInferenceTaskArgs,
        scratch: PredictionScratchSpace,
        dataset_path: UPath,
        model_stage_paths: ModelStagePaths,
    ) -> RunInferenceTaskResults:
        """
        Run inference using legacy OlmoEarthRunConfig with env vars and CLI overrides.

        TODO chrisw: delete this code path once we've fully migrated to the unified config.
        """
        logger.info("Using legacy config path")
        olmoearth_run_config = OlmoEarthRunConfigLoader.load_olmoearth_run_config(model_stage_paths.olmoearth_run_config_path)

        rslearn_env_vars = RslearnTemplateVars(
            DATASET_PATH=str(dataset_path),
            EXTRA_FILES_PATH=str(model_stage_paths.extra_model_files_path),
            TRAINER_DATA_PATH=str(model_stage_paths.trainer_checkpoints_path),
            NUM_WORKERS=OlmoEarthSettings.NUM_WORKERS,
            PREDICTION_OUTPUT_LAYER=LEGACY_WINDOW_OUTPUT_LAYER_NAME,
            WANDB_PROJECT=None,  # Inference doesn't need wandb logging
            WANDB_NAME=None,     # Inference doesn't need wandb logging
            WANDB_ENTITY=None,   # Inference doesn't need wandb logging
        )

        # TODO: how much of the rest of this can go in RslearnTemplateVars?
        for partition_id in task_args.partition_ids:
            logger.info(f"Running inference step for partition {partition_id}")
            rslearn_groups = [scratch.get_group(partition_id)]
            predict_args = [
                "predict",
                "--config", model_stage_paths.model_config_path,
                "--ckpt_path", model_stage_paths.checkpoint_path,
                # only run inference on the group
                "--data.predict_config.groups", json.dumps(rslearn_groups),
                "--trainer.logger", "false",  # disable wandb logging
                "--data.init_args.predict_config.output_layer", LEGACY_WINDOW_OUTPUT_LAYER_NAME,
            ]
            logger.debug(f"Setting rslearn env vars: {rslearn_env_vars}")
            logger.info(f"Running inference on groups {rslearn_groups} with args: {predict_args}")
            with rslearn_env_vars.temp_env():
                self._run_inference_for_groups(predict_args)

        return RunInferenceTaskResults(inference_results_data_type=olmoearth_run_config.inference_results_config.data_type)

    def _run_inference_for_groups(self, predict_args: list[str]) -> None:
        # We need to catch SystemExit because rslearn or any of its dependencies might call sys.exit() which will
        # wrest control away from us and crash the step without informing the orchestrator.
        try:
            RslearnLightningCLI(
                model_class=RslearnLightningModule,
                datamodule_class=RslearnDataModule,
                parser_class=RslearnArgumentParser,
                args=predict_args,
                subclass_mode_model=True,
                subclass_mode_data=True,
                save_config_kwargs={"overwrite": True},
            )
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError(f"rslearn exited with code {e.code}") from e
