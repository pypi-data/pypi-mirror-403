from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class PostprocessorName(StrEnum):
    NOOP = "noop"
    COMBINE_GEOTIFF = "combine_geotiff"


class NoopPostprocessor(BaseModel):
    """Postprocessor that does nothing."""
    name: Literal[PostprocessorName.NOOP]


class LinearValueTransformConfig(BaseModel):
    """Linear transform: output = scale * input + offset.

    Uses discriminated union pattern to support other transform types in the future.
    """
    type: Literal["linear"] = "linear"
    scale: float = 1.0
    offset: float = 0.0
    output_dtype: Literal["uint8", "int16", "int32", "float32"] | None = Field(
        default=None,
        description="The output dtype to transform to. If not specified, the output dtype will be the same as the input dtype."
    )


# Discriminated union for future extensibility (e.g., LogTransformConfig, etc.)
ValueTransformConfig = Annotated[LinearValueTransformConfig, Field(discriminator="type")]


class CombineGeotiff(BaseModel):
    """Postprocessor that combines the geotiffs into a single geotiff."""
    name: Literal[PostprocessorName.COMBINE_GEOTIFF]
    max_pixels_per_dimension: int = 10_000
    value_transform: ValueTransformConfig | None = None


Postprocessor = TypeAliasType(
    "Postprocessor",
    Annotated[
        NoopPostprocessor | CombineGeotiff,
        Field(discriminator="name")
    ]
)


class Postprocessors(BaseModel):
    window: Postprocessor = Field(description="Controls the postprocessing of the prediction results for a single window.")
    partition: Postprocessor = Field(description="Controls the postprocessing of all the window results for a single partition.")
    request: Postprocessor = Field(description="Controls the postprocessing of all the partition results for the entire request.")
