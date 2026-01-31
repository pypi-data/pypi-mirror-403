"""Utilities for loading and processing spatial masks for inference filtering."""
import json
import logging
from typing import Any, Literal, cast

import numpy as np
import rasterio  # type: ignore[import-untyped]
from affine import Affine  # type: ignore[import-untyped]
from rasterio.crs import CRS  # type: ignore[import-untyped]
from rasterio.session import GSSession, DummySession  # type: ignore[import-untyped]
from pydantic import BaseModel, Field
from rasterio.warp import reproject, Resampling, transform_bounds  # type: ignore[import-untyped]
from rasterio.features import geometry_mask  # type: ignore[import-untyped]
from rslearn.utils.geometry import Projection, STGeometry, WGS84_PROJECTION, WGS84_EPSG
from shapely import box
from shapely.geometry import shape, mapping
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union, transform as shapely_transform
from shapely.prepared import prep
from pyproj import Transformer

from olmoearth_shared.api.run.prediction_geometry import PredictionResultCollection
from olmoearth_shared.tools.gcs_tools import (
    is_gcs_path,
    list_gcs_directory,
    read_text_from_gcs,
)

logger = logging.getLogger(__name__)


class MaskConfig:
    """Configuration for spatial masking, bundling mask files with their valid values."""

    def __init__(self, mask_files: list["MaskFileInfo"], valid_values: list[int]):
        self.mask_files = mask_files
        self.valid_values = valid_values

    @classmethod
    def from_gcs_path(cls, gcs_path: str | None, valid_values: list[int]) -> "MaskConfig | None":
        """Load mask config from a GCS path. Returns None if gcs_path is None."""
        if not gcs_path:
            return None
        mask_files = MaskFileInfo.load_mask_files(gcs_path)
        return cls(mask_files, valid_values)


class MaskFileInfo(BaseModel):
    """Information about a mask file."""

    model_config = {"arbitrary_types_allowed": True}

    path: str = Field(description="Path to the mask file (GCS or local)")
    bounding_box: BaseGeometry = Field(description="Bounding box in WGS84")
    file_type: Literal["geotiff", "geojson"] = Field(description="Type of mask file")

    def to_stgeometry(self) -> STGeometry:
        """Returns the mask bounding box as an STGeometry in WGS84."""
        return STGeometry(WGS84_PROJECTION, self.bounding_box, time_range=None)

    @staticmethod
    def load_mask_files(gcs_path: str) -> list["MaskFileInfo"]:
        """Load mask file infos from a GCS path (single file or directory)."""
        mask_files = MaskFileInfo._list_mask_files(gcs_path)
        logger.info(f"Loading {len(mask_files)} mask files from {gcs_path}")
        return [MaskFileInfo._get_mask_file_info(mask_file) for mask_file in mask_files]

    @staticmethod
    def _list_mask_files(gcs_path: str) -> list[str]:
        """List mask files from a GCS path (single file or directory)."""
        if gcs_path.endswith(".tif") or gcs_path.endswith(".geojson"):
            return [gcs_path]

        # It's a directory - list files
        all_files = list_gcs_directory(gcs_path)
        mask_files = [f for f in all_files if f.endswith(".tif") or f.endswith(".geojson")]

        if not mask_files:
            raise ValueError(f"No mask files (.tif or .geojson) found in {gcs_path}")

        # Validate all files are same type
        tif_files = [f for f in mask_files if f.endswith(".tif")]
        geojson_files = [f for f in mask_files if f.endswith(".geojson")]

        if tif_files and geojson_files:
            raise ValueError(f"Mixed mask types. Found {len(tif_files)} .tif and {len(geojson_files)} .geojson files.")

        return mask_files

    @staticmethod
    def _get_geotiff_info(file_path: str) -> "MaskFileInfo":
        """Get mask info from a GeoTIFF file by reading only the header. Reads directly from GCS."""
        session = GSSession() if is_gcs_path(file_path) else DummySession()
        with rasterio.Env(session=session), rasterio.open(file_path) as src:
            # Convert bounds to WGS84
            wgs84_bounds = transform_bounds(src.crs, CRS.from_epsg(WGS84_EPSG), *src.bounds)
            wgs84_box = box(*wgs84_bounds)
            return MaskFileInfo(
                path=file_path,
                bounding_box=wgs84_box,
                file_type="geotiff",
            )

    @staticmethod
    def _get_geojson_info(mask_path: str) -> "MaskFileInfo":
        """Get mask info from GeoJSON text content."""
        geometries = get_shapes_from_geojson_file(mask_path)
        if not geometries:
            raise ValueError(f"No geometries found in GeoJSON file: {mask_path}")

        combined = unary_union(geometries)

        # GeoJSON is already WGS84 - convert to bounding box
        return MaskFileInfo(path=mask_path, bounding_box=box(*combined.bounds), file_type="geojson")

    @staticmethod
    def _get_mask_file_info(mask_path: str) -> "MaskFileInfo":
        """Get mask info for a single file."""
        if mask_path.endswith(".tif"):
            return MaskFileInfo._get_geotiff_info(mask_path)
        elif mask_path.endswith(".geojson"):
            return MaskFileInfo._get_geojson_info(mask_path)
        else:
            raise ValueError(f"Unsupported mask file type: {mask_path}")


def get_shapes_from_geojson_file(geojson_path: str) -> list[BaseGeometry]:
    if is_gcs_path(geojson_path):
        geojson_text = read_text_from_gcs(geojson_path)
    else:
        with open(geojson_path, "r") as f:
            geojson_text = f.read()
    geojson = json.loads(geojson_text)

    if geojson.get("type") == "FeatureCollection":
        geometries = [shape(f["geometry"]) for f in geojson["features"] if f.get("geometry")]
    elif geojson.get("type") == "Feature":
        geometries = [shape(geojson["geometry"])]
    else:
        geometries = [shape(geojson)]
    return geometries


def get_first_intersecting_mask_file(mask_infos: list[MaskFileInfo], geometry: STGeometry) -> MaskFileInfo | None:
    """Get the first mask file whose bounding box intersects with the given geometry."""
    geometry_wgs84 = geometry.to_projection(WGS84_PROJECTION)
    for info in mask_infos:
        if info.bounding_box.intersects(geometry_wgs84.shp):
            return info
    return None


def get_first_intersecting_mask_for_raster(
    mask_infos: list[MaskFileInfo],
    bounds: tuple[float, float, float, float],
    crs: CRS,
) -> MaskFileInfo | None:
    """Get the first mask file whose bounds intersect with the given raster bounds.

    Args:
        mask_infos: List of mask file info objects to search
        bounds: Raster bounds as (left, bottom, right, top)
        crs: CRS of the raster bounds
    """
    if not mask_infos:
        return None
    wgs84_bounds = transform_bounds(crs, CRS.from_epsg(WGS84_EPSG), *bounds)
    raster_geom = box(*wgs84_bounds)
    for info in mask_infos:
        if info.bounding_box.intersects(raster_geom):
            return info
    return None


def _window_intersects_raster_mask(mask_file: MaskFileInfo, window_geometry: STGeometry, valid_values: list[int]) -> bool:
    """Check if a GeoTIFF mask has valid pixels within window bounds. Reads directly from GCS."""
    session = GSSession() if is_gcs_path(mask_file.path) else DummySession()
    with rasterio.Env(session=session), rasterio.open(mask_file.path) as src:
        # Transform query geometry to mask CRS
        mask_projection = Projection(src.crs, x_resolution=1, y_resolution=1)
        query_in_mask_crs = window_geometry.to_projection(mask_projection)
        query_bounds = cast(BaseGeometry, query_in_mask_crs.shp).bounds

        # Create a window from the bounds
        window = rasterio.windows.from_bounds(*query_bounds, src.transform)

        # Clamp window to valid range
        window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))

        if window.width <= 0 or window.height <= 0:
            return False

        # Read the data in the window
        data = src.read(1, window=window)

        # Check if any valid values exist
        return bool(np.isin(data, valid_values).any())


def _window_intersects_vector_mask(mask_file: MaskFileInfo, window_geometry: STGeometry) -> bool:
    """Check if a GeoJSON mask intersects with geometry. Reads directly from GCS."""
    geometries = get_shapes_from_geojson_file(mask_file.path)

    # GeoJSON is always WGS84 - convert query geometry to WGS84
    query_wgs84 = window_geometry.to_projection(WGS84_PROJECTION)
    return any(geom.intersects(query_wgs84.shp) for geom in geometries)


def window_intersects_valid_mask(window_geometry: STGeometry, mask_info: MaskFileInfo | None, valid_values: list[int]) -> bool:
    """
    Check if a window intersects with valid pixels in the mask.
    This method is used to determine if we should inference on a window at all.
    """
    if mask_info is None:
        return False

    if mask_info.file_type == "geotiff":
        return _window_intersects_raster_mask(mask_info, window_geometry, valid_values)
    else:
        return _window_intersects_vector_mask(mask_info, window_geometry)


def apply_mask_to_raster_data(
    data: np.ndarray,
    transform: Affine,
    crs: CRS,
    mask_info: MaskFileInfo | None,
    valid_values: list[int],
    nodata_value: int | float = 0,
) -> None:
    """Apply mask to numpy array in-place, setting pixels outside valid mask areas to nodata."""
    # Determine array shape (handles both 2D and 3D arrays)
    if data.ndim == 3:
        height, width = data.shape[1], data.shape[2]
    else:
        height, width = data.shape[0], data.shape[1]

    if mask_info is None:
        # No mask - set entire array to nodata
        data[:] = nodata_value
        return

    # Build mask array (True = valid, False = masked)
    if mask_info.file_type == "geotiff":
        mask_array = _reproject_geotiff_mask(mask_info, transform, crs, height, width, valid_values)
    else:
        mask_array = _rasterize_geojson_mask(mask_info, transform, crs, height, width)

    # Apply mask to array
    # `mask_array` is (height, width). For 3D rasters we use bands-first (bands, height, width),
    # so `data[:, ~mask_array]` selects all bands at the invalid pixels.
    if data.ndim == 3:
        # Bands-first: (bands, height, width)
        data[:, ~mask_array] = nodata_value
    else:
        data[~mask_array] = nodata_value


def _reproject_geotiff_mask(
    mask_info: MaskFileInfo,
    dst_transform: Affine,
    dst_crs: CRS,
    height: int,
    width: int,
    valid_values: list[int],
) -> np.ndarray:
    """Load  a GeoTIFF mask and return the re-projected array of valid pixels"""
    mask_path = mask_info.path
    session = GSSession() if is_gcs_path(mask_path) else DummySession()
    with rasterio.Env(session=session), rasterio.open(mask_path) as src:
        mask_data = np.zeros((height, width), dtype=src.dtypes[0])

        reproject(
            source=rasterio.band(src, 1),
            destination=mask_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest,
        )

        result_mask = np.zeros((height, width), dtype=bool)
        for val in valid_values:
            result_mask |= (mask_data == val)
        return result_mask


def _rasterize_geojson_mask(
    mask_info: MaskFileInfo,
    dst_transform: Affine,
    dst_crs: CRS,
    height: int,
    width: int,
) -> np.ndarray:
    """Apply a GeoJSON mask and return the mask array."""
    geometries = get_shapes_from_geojson_file(mask_info.path)

    # Transform geometries from WGS84 to raster CRS
    transformer = Transformer.from_crs(f"EPSG:{WGS84_EPSG}", dst_crs, always_xy=True)
    transformed_geometries = [
        mapping(shapely_transform(transformer.transform, shp))
        for shp in geometries
    ]

    return geometry_mask(transformed_geometries, out_shape=(height, width), transform=dst_transform, invert=True)


def filter_features_by_mask(
    feature_collection: PredictionResultCollection,
    mask_info: MaskFileInfo | None,
    valid_values: list[int],
) -> PredictionResultCollection:
    """Filter a FeatureCollection to only include features that intersect with the mask."""
    if mask_info is None:
        return feature_collection

    # Convert features to shapely geometries once
    features_with_geoms: list[tuple[Any, BaseGeometry]] = []
    for feature in feature_collection.features:
        if feature.geometry is not None:
            features_with_geoms.append((feature, shape(feature.geometry.model_dump())))

    matched_features: list[Any] = []

    if mask_info.file_type == "geojson":
        # Vector mask - load geometries once and prepare for efficient intersection
        mask_geometries = get_shapes_from_geojson_file(mask_info.path)
        combined_mask = prep(unary_union(mask_geometries))
        for feature, geom in features_with_geoms:
            if combined_mask.intersects(geom):
                matched_features.append(feature)
    else:
        # Raster mask - open file once, check all features
        session = GSSession() if is_gcs_path(mask_info.path) else DummySession()
        with rasterio.Env(session=session), rasterio.open(mask_info.path) as src:
            transformer = Transformer.from_crs(f"EPSG:{WGS84_EPSG}", src.crs, always_xy=True)

            for feature, geom in features_with_geoms:
                geom_in_mask_crs = shapely_transform(transformer.transform, geom)
                query_bounds = geom_in_mask_crs.bounds

                window = rasterio.windows.from_bounds(*query_bounds, src.transform)
                window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))

                if window.width <= 0 or window.height <= 0:
                    continue

                data = src.read(1, window=window)
                if np.isin(data, valid_values).any():
                    matched_features.append(feature)

    return PredictionResultCollection(type="FeatureCollection", features=matched_features)
