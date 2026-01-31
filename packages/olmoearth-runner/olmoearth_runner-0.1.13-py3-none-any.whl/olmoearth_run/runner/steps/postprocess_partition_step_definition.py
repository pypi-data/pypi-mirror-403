import logging
from multiprocessing import Pool
from typing import cast

from rslearn.dataset import Dataset, Window
from upath import UPath

from olmoearth_run.config import OlmoEarthSettings
from olmoearth_run.runner.steps.base_step_definition import BaseStepDefinition
from olmoearth_run.runner.tools.mask_utils import MaskConfig, get_first_intersecting_mask_file, filter_features_by_mask
from olmoearth_run.runner.tools.olmoearth_config.loaders.config import ConfigClassLoader
from olmoearth_run.runner.tools.olmoearth_config.loaders.prediction_tools import PredictionToolsClassLoader
from olmoearth_run.runner.tools.olmoearth_config.utils import ConfigUtils
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster, \
    PostprocessInterfaceVector
from olmoearth_run.shared.models.api.task_args import PostprocessPartitionTaskArgs
from olmoearth_run.shared.models.api.task_results import InferenceResultsDataType, PostprocessPartitionTaskResults
from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_run.shared.models.prediction_scratch_space import PredictionScratchSpace, \
    LEGACY_WINDOW_OUTPUT_LAYER_NAME, LEGACY_WINDOW_OUTPUT_BAND_NAME
from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig

logger = logging.getLogger(__name__)


class PostprocessPartitionStepDefinition(BaseStepDefinition[PostprocessPartitionTaskArgs, PostprocessPartitionTaskResults]):
    scratch: PredictionScratchSpace
    config: OlmoEarthRunConfig | OlmoEarthConfig
    output_band_dir: str

    def run(self, task_args: PostprocessPartitionTaskArgs) -> PostprocessPartitionTaskResults:
        self.scratch = PredictionScratchSpace(root_path=task_args.scratch_path)
        model_stage_paths = ModelStagePaths(root_path=task_args.model_stage_root_path)

        dataset = Dataset(UPath(task_args.dataset_path))

        # Load config - check for unified config first
        olmoearth_config_path = UPath(self.scratch.olmoearth_config_path)
        if olmoearth_config_path.exists():
            self.config = ConfigClassLoader.load_olmoearth_config(str(olmoearth_config_path))
            result_data_type = ConfigUtils.get_output_data_type(self.config)
            self.output_band_dir = ConfigUtils.get_output_band_dir(self.config)
        else:
            self.config = OlmoEarthRunConfigLoader.load_olmoearth_run_config(model_stage_paths.olmoearth_run_config_path)
            result_data_type = self.config.inference_results_config.data_type
            self.output_band_dir = LEGACY_WINDOW_OUTPUT_BAND_NAME

        # Load mask configuration if provided
        mask_config: MaskConfig | None = None
        if task_args.mask_gcs_path:
            logger.info(f"Loading mask from {task_args.mask_gcs_path} for postprocessing")
            mask_config = MaskConfig.from_gcs_path(task_args.mask_gcs_path, task_args.mask_valid_values)

        output_files: list[UPath] = []
        for partition_id in task_args.partition_ids:
            rslearn_groups = [self.scratch.get_group(partition_id)]
            logger.info(f"Loading windows for partition {partition_id} with groups {rslearn_groups}")
            windows = dataset.storage.get_windows(groups=rslearn_groups)
            if result_data_type == InferenceResultsDataType.VECTOR:
                output_files.extend(self._postprocess_vector(partition_id, windows, mask_config))
            else:
                output_files.extend(self._postprocess_raster(partition_id, windows, mask_config))

        return PostprocessPartitionTaskResults(
            partition_ids=task_args.partition_ids,
            output_files=[str(f) for f in output_files],
            inference_results_data_type=result_data_type,
        )

    def _postprocess_raster(
        self,
        partition_id: str,
        windows: list[Window],
        mask_config: MaskConfig | None,
    ) -> list[UPath]:
        window_postprocessor = cast(PostprocessInterfaceRaster, PredictionToolsClassLoader.load_window_postprocessor(self.config))

        # Prepare arguments for parallel processing
        process_args = [
            (window, self.scratch.root_path, window_postprocessor, partition_id, self.output_band_dir)
            for window in windows
        ]

        logger.debug(f"Postprocessing raster partition {partition_id} with {len(windows)} windows using {window_postprocessor}")
        # Use multiprocessing to process windows in parallel
        with Pool(processes=OlmoEarthSettings.NUM_WORKERS) as pool:
            window_output_paths = pool.starmap(_process_raster_window, process_args)

        partition_postprocessor = cast(PostprocessInterfaceRaster, PredictionToolsClassLoader.load_partition_postprocessor(self.config))

        # Configure masking on the partition postprocessor
        if mask_config and hasattr(partition_postprocessor, 'set_mask_config'):
            partition_postprocessor.set_mask_config(mask_config)

        logger.debug(f"Postprocessing raster partition {partition_id} using {partition_postprocessor}")
        partition_result_raster_dir = self.scratch.get_partition_result_raster_dir(partition_id)
        partition_result_raster_dir.mkdir(parents=True, exist_ok=True)
        saved_raster_paths = partition_postprocessor.process_partition(window_output_paths, partition_result_raster_dir)

        return saved_raster_paths

    def _postprocess_vector(
        self,
        partition_id: str,
        windows: list[Window],
        mask_config: MaskConfig | None,
    ) -> list[UPath]:
        window_postprocessor = cast(PostprocessInterfaceVector, PredictionToolsClassLoader.load_window_postprocessor(self.config))

        # Prepare arguments for parallel processing
        process_args = [
            (window, self.scratch.root_path, window_postprocessor, partition_id, mask_config)
            for window in windows
        ]

        logger.debug(f"Postprocessing vector partition {partition_id} with {len(windows)} windows using {window_postprocessor}")
        # Use multiprocessing to process windows in parallel
        with Pool(processes=OlmoEarthSettings.NUM_WORKERS) as pool:
            window_results = pool.starmap(_process_vector_window, process_args)

        # Filter out None results (windows with no output)
        all_window_results = [result for result in window_results if result is not None]

        # Combine all window results to produce a single result for the partition
        partition_postprocessor = cast(PostprocessInterfaceVector, PredictionToolsClassLoader.load_partition_postprocessor(self.config))
        logger.debug(f"Postprocessing vector partition {partition_id} using {partition_postprocessor}")
        partition_result = partition_postprocessor.process_partition(all_window_results)
        self.scratch.write_partition_result_vector(partition_id, partition_result)

        return [self.scratch.get_partition_result_vector_path(partition_id)]


def _process_raster_window(window: Window, scratch_path: str, window_postprocessor: PostprocessInterfaceRaster, partition_id: str, output_band_dir: str) -> UPath:
    scratch = PredictionScratchSpace(root_path=scratch_path)

    # this path is dictated by the RslearnWriter configuration in RunInferenceStepDefinition
    window_output_path = scratch.get_window_prediction_result_geotiff_path(
        window.get_layer_dir(LEGACY_WINDOW_OUTPUT_LAYER_NAME),
        band_dir=output_band_dir,
    )

    # retrieve the GeoJSON Feature from which the window was derived
    window_group = scratch.get_group(partition_id)
    window_root = window.storage.get_window_root(window_group, window.name)
    request_feature = scratch.get_window_request_feature(window_root)

    logger.debug(f"Postprocessing raster window {window.name} with output path {window_output_path}")
    # the postprocessor updates the geotiff in place
    window_postprocessor.process_window(request_feature, window_output_path)
    return window_output_path


def _process_vector_window(window: Window, scratch_path: str, window_postprocessor: PostprocessInterfaceVector, partition_id: str, mask_config: MaskConfig | None) -> PredictionResultCollection | None:
    scratch = PredictionScratchSpace(root_path=scratch_path)

    # retrieve the inference result GeoJSON FeatureCollection
    output = scratch.get_window_prediction_result_collection(window.get_layer_dir('output'))
    if output is None:
        logger.warning(f"no output generated for window {window.name}")
        return None

    # retrieve the GeoJSON Feature from which the window was derived
    window_group = scratch.get_group(partition_id)
    window_root = window.storage.get_window_root(window_group, window.name)
    request_feature = scratch.get_window_request_feature(window_root)

    # generate a complete result for the window, derived from combining the request feature and the output
    window_result = window_postprocessor.process_window(request_feature, output)

    if mask_config:
        mask_file = get_first_intersecting_mask_file(mask_config.mask_files, window.get_geometry())
        window_result = filter_features_by_mask(window_result, mask_file, mask_config.valid_values)

    # writing each result to the Window isn't necessary, but it's a helpful artifact
    scratch.write_window_result_vector(window_root, window_result)

    return window_result
