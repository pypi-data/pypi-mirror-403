import logging

import yaml
from rslearn.config import dataset
from upath import UPath

from olmoearth_run.runner.models.operational_context import DataSource, DatasetOperationalContext, ModelOperationalContext
from olmoearth_run.runner.models import rslearn_config
from olmoearth_run.runner.tools.olmoearth_config.loaders.config import ConfigClassLoader
from olmoearth_run.runner.tools.olmoearth_config.transpilers.dataset.label_output_layers import LabelOutputLayers
from olmoearth_run.runner.tools.olmoearth_config.transpilers.dataset.modality_layers import ModalityLayers
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.data import DataTranspiler
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.lightning_module import LightningModuleTranspiler
from olmoearth_run.runner.tools.olmoearth_config.transpilers.model.trainer import TrainerTranspiler
from olmoearth_run.shared.models.model_stage_paths import DATASET_CONFIG_FILE_NAME_IN_DATASET_DIR
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig

logger = logging.getLogger(__name__)


def to_dataset_config(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> dataset.DatasetConfig:
    """Converts OlmoEarthConfig to rslearn's dataset config object."""
    return dataset.DatasetConfig(
        layers={
            **ModalityLayers.generate_modality_layers(olmoearth_config, ops_context),
            **LabelOutputLayers.generate_label_and_output_layers(olmoearth_config, ops_context)
        },
    )


def to_dataset_config_json(olmoearth_config: OlmoEarthConfig, ops_context: DatasetOperationalContext) -> str:
    """Converts OlmoEarthConfig to rslearn's dataset config as a JSON string."""
    config = to_dataset_config(olmoearth_config, ops_context)
    return config.model_dump_json(exclude_defaults=True, indent=2)


def to_model_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> rslearn_config.ModelYamlConfig:
    """Converts OlmoEarthConfig to rslearn's model config object."""
    return rslearn_config.ModelYamlConfig(
        model=LightningModuleTranspiler.generate_lightning_module_config(olmoearth_config, ops_context),
        data=DataTranspiler.generate_data_module_config(olmoearth_config, ops_context),
        trainer=TrainerTranspiler.generate_trainer_config(olmoearth_config, ops_context),
    )


def to_model_config_yaml(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext) -> str:
    """Converts OlmoEarthConfig to rslearn's model config as a YAML string."""
    config = to_model_config(olmoearth_config, ops_context)
    return yaml.dump(config.model_dump(mode="json", exclude_defaults=True), default_flow_style=False, sort_keys=False)


def transpile_and_write_dataset_config(olmoearth_config_path: str, dataset_path: UPath) -> None:
    """Transpile OlmoEarthConfig to rslearn DatasetConfig and write to dataset_path/config.json."""
    logger.info(f"Loading OlmoEarthConfig from {olmoearth_config_path}")
    config = ConfigClassLoader.load_olmoearth_config(olmoearth_config_path)

    ops_context = DatasetOperationalContext(
        data_source=DataSource.PLANETARY_COMPUTER,
        dataset_path=str(dataset_path),
    )

    config_path = dataset_path / DATASET_CONFIG_FILE_NAME_IN_DATASET_DIR
    logger.info(f"Writing transpiled dataset config to {config_path}")
    config_path.write_text(to_dataset_config_json(config, ops_context))


def transpile_and_write_model_config(olmoearth_config: OlmoEarthConfig, ops_context: ModelOperationalContext, output_path: UPath) -> None:
    """Transpile OlmoEarthConfig to rslearn model.yaml and write to output_path."""
    logger.info(f"Writing transpiled model config to {output_path}")
    output_path.write_text(to_model_config_yaml(olmoearth_config, ops_context))
