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
from olmoearth_run.runner.tools.olmoearth_config.transpilers.olmoearth_to_rslearn import to_model_config_yaml
from olmoearth_run.shared.models.api.step_type import StepType
from olmoearth_run.shared.models.api.task_args import ModelEvaluationTaskArgs
from olmoearth_run.shared.models.api.task_results import ModelEvaluationTaskResults
from olmoearth_run.shared.models.fine_tuning_scratch_space import FineTuningScratchSpace

logger = logging.getLogger(__name__)


class ModelEvaluationStepDefinition(BaseStepDefinition[ModelEvaluationTaskArgs, ModelEvaluationTaskResults]):
    def run(self, task_args: ModelEvaluationTaskArgs) -> ModelEvaluationTaskResults:
        logger.info("Starting model evaluation step")

        scratch_space = FineTuningScratchSpace(root_path=task_args.scratch_path)

        if not UPath(scratch_space.olmoearth_config_path).exists():
            logger.info("Unified OlmoEarthConfig not found. Skipping model evaluation for legacy config workflow.")
            return ModelEvaluationTaskResults()

        evaluation_config_path = self._transpile_config_for_evaluation(scratch_space)

        predict_args = [
            "predict",
            "--config", str(evaluation_config_path),
            "--ckpt_path", task_args.checkpoint_path,
        ]

        logger.info(f"Running evaluation prediction with args: {predict_args}")
        self._run_evaluation_prediction(predict_args)
        # TODO: Add logic to read predictions from the dataset path and calculate evaluation metrics
        #   1. Read model_evaluation_metadata.json from dataset_path (to get patch bound info)
        #   2. For each window, read predictions and labels from the output layer
        #   3. Mask out nodata values
        #   5. Calculate metrics (confusion matrix, per-class metrics, etc.) on the masked predictions and labels

        logger.info("Model evaluation completed successfully")
        return ModelEvaluationTaskResults()

    def _transpile_config_for_evaluation(self, scratch_space: FineTuningScratchSpace) -> UPath:
        config = ConfigClassLoader.load_olmoearth_config(scratch_space.olmoearth_config_path)

        model_stage_paths = scratch_space.model_stage_paths
        ops_context = ModelOperationalContext(
            step_type=StepType.MODEL_EVALUATION,
            dataset_path=model_stage_paths.default_dataset_path,
            num_data_worker_processes=OlmoEarthSettings.NUM_WORKERS,
            model_stage_paths=model_stage_paths,
        )

        # Write evaluation config to a separate file to avoid overwriting the training config
        evaluation_config_path = UPath(scratch_space.model_evaluation_config_path)
        evaluation_config_path.write_text(to_model_config_yaml(config, ops_context))

        return evaluation_config_path

    def _run_evaluation_prediction(self, predict_args: list[str]) -> None:
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
