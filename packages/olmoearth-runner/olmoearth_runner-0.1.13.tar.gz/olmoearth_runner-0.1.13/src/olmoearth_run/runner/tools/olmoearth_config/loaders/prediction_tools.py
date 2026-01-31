from typing import assert_never

from rslearn.utils import Projection as RsLearnProjection

from olmoearth_run.runner.tools.olmoearth_config.utils import ConfigUtils, OutputFieldUtils
from olmoearth_run.runner.tools.partitioners.partition_interface import PartitionInterface
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader
from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_shared.models.olmoearth_config.prediction_requests.partitioners import Partitioner as PartitionerConfig
from olmoearth_run.runner.tools.partitioners.noop_partitioner import NoopPartitioner as NoopPartitionerImpl
from olmoearth_run.runner.tools.partitioners.grid_partitioner import GridPartitioner as GridPartitionerImpl
from olmoearth_shared.models.olmoearth_config.prediction_requests.partitioners import NoopPartitioner as NoopPartitionerConfig, GridPartitioner as GridPartitionerConfig
from olmoearth_shared.models.olmoearth_config.prediction_requests.projections import UseUTMProjection, CRSProjection
from olmoearth_run.runner.tools.postprocessors.postprocess_interface import PostprocessInterfaceRaster as PostprocessInterfaceRasterImpl, PostprocessInterfaceVector as PostprocessInterfaceVectorImpl
from olmoearth_run.runner.tools.postprocessors.noop_raster import NoopRaster as NoopRasterImpl
from olmoearth_shared.models.olmoearth_config.prediction_requests.postprocessors import Postprocessor as PostprocessorConfig
from olmoearth_shared.models.olmoearth_config.prediction_requests.postprocessors import NoopPostprocessor as NoopPostprocessorConfig, CombineGeotiff as CombineGeotiffConfig, LinearValueTransformConfig
from olmoearth_run.runner.tools.postprocessors.combine_geotiff import CombineGeotiff as CombineGeotiffImpl, LinearValueTransform as LinearValueTransformImpl


class PredictionToolsClassLoader:
    @staticmethod
    def load_request_to_partitions_partitioner(config: OlmoEarthRunConfig | OlmoEarthConfig) -> PartitionInterface:
        """Loads and initializes a partitioner based on the OlmoEarthRun configuration."""
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_partition_request_geometry_partitioner(config)

        if not config.prediction_requests:
            raise ValueError("Prediction requests configuration is required but not found in OlmoEarthConfig")

        return PredictionToolsClassLoader.load_partitioner_from_config(config.prediction_requests.partitioners.request_to_partitions, config)

    @staticmethod
    def load_partition_to_windows_partitioner(config: OlmoEarthRunConfig | OlmoEarthConfig) -> PartitionInterface:
        """Loads and initializes a partitioner based on the OlmoEarthRun configuration."""
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_prepare_window_geometries_partitioner(config)

        if not config.prediction_requests:
            raise ValueError("Prediction requests configuration is required but not found in OlmoEarthConfig")

        return PredictionToolsClassLoader.load_partitioner_from_config(config.prediction_requests.partitioners.partition_to_windows, config)

    @staticmethod
    def load_partitioner_from_config(partitioner_config: PartitionerConfig, olmoearth_config: OlmoEarthConfig) -> PartitionInterface:
        """Loads and initializes a partitioner based on the OlmoEarthRun configuration."""
        match partitioner_config:
            case NoopPartitionerConfig():
                return NoopPartitionerImpl()
            case GridPartitionerConfig():
                return PredictionToolsClassLoader.load_grid_partitioner(partitioner_config, olmoearth_config)
            case unreachable:
                assert_never(unreachable)

    @staticmethod
    def load_grid_partitioner(partitioner_config: GridPartitionerConfig, olmoearth_config: OlmoEarthConfig) -> GridPartitionerImpl:
        output_projection: RsLearnProjection | None = None
        use_utm: bool = False

        match partitioner_config.projection:
            case UseUTMProjection():
                window_resolution = ConfigUtils.get_window_resolution(olmoearth_config)
                output_projection = RsLearnProjection(
                    "EPSG:3857",  # arbitrary and ignored in this case
                    window_resolution,
                    -window_resolution
                )
                use_utm = True
            case CRSProjection(crs=crs, x_resolution=x_resolution, y_resolution=y_resolution):
                output_projection = RsLearnProjection(crs, x_resolution, y_resolution)
                use_utm = False
            case None:
                pass
            case unreachable:
                assert_never(unreachable)

        return GridPartitionerImpl(
            grid_size=partitioner_config.grid_size,
            overlap_size=partitioner_config.overlap_size,
            output_projection=output_projection,
            use_utm=use_utm,
            clip=partitioner_config.clip
        )

    @staticmethod
    def load_window_postprocessor(config: OlmoEarthRunConfig | OlmoEarthConfig) -> PostprocessInterfaceRasterImpl | PostprocessInterfaceVectorImpl:
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_window_postprocessor(config)

        if not config.prediction_requests:
            raise ValueError("Prediction requests configuration is required but not found in OlmoEarthConfig")

        return PredictionToolsClassLoader.load_postprocessor_from_config(config.prediction_requests.postprocessors.window, config)

    @staticmethod
    def load_partition_postprocessor(config: OlmoEarthRunConfig | OlmoEarthConfig) -> PostprocessInterfaceRasterImpl | PostprocessInterfaceVectorImpl:
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_partition_postprocessor(config)

        if not config.prediction_requests:
            raise ValueError("Prediction requests configuration is required but not found in OlmoEarthConfig")

        return PredictionToolsClassLoader.load_postprocessor_from_config(config.prediction_requests.postprocessors.partition, config)

    @staticmethod
    def load_request_postprocessor(config: OlmoEarthRunConfig | OlmoEarthConfig) -> PostprocessInterfaceRasterImpl | PostprocessInterfaceVectorImpl:
        if isinstance(config, OlmoEarthRunConfig):
            return OlmoEarthRunConfigLoader.get_dataset_postprocessor(config)

        if not config.prediction_requests:
            raise ValueError("Prediction requests configuration is required but not found in OlmoEarthConfig")

        return PredictionToolsClassLoader.load_postprocessor_from_config(config.prediction_requests.postprocessors.request, config)

    @staticmethod
    def load_postprocessor_from_config(postprocessor_config: PostprocessorConfig, olmoearth_config: OlmoEarthConfig) -> PostprocessInterfaceRasterImpl | PostprocessInterfaceVectorImpl:
        match postprocessor_config:
            case NoopPostprocessorConfig():
                return NoopRasterImpl()
            case CombineGeotiffConfig():
                raster_output_field = ConfigUtils.get_raster_output_field(olmoearth_config)
                nodata_value = OutputFieldUtils.get_nodata_for_field(raster_output_field)
                value_transform = None
                if postprocessor_config.value_transform:
                    match postprocessor_config.value_transform:
                        case LinearValueTransformConfig():
                            value_transform = LinearValueTransformImpl(
                                type="linear",
                                scale=postprocessor_config.value_transform.scale,
                                offset=postprocessor_config.value_transform.offset,
                                output_dtype=postprocessor_config.value_transform.output_dtype,
                            )
                return CombineGeotiffImpl(
                    nodata_value=nodata_value if nodata_value is not None else 0,
                    max_pixels_per_dimension=postprocessor_config.max_pixels_per_dimension,
                    value_transform=value_transform,
                )
            case unreachable:
                assert_never(unreachable)
