"""Utilities for common project tasks."""

import re
from collections.abc import Callable, Iterable
from uuid import UUID, uuid5

from dagster import InputContext
from dagster_aws.s3 import S3Resource
from geojson import Feature, FeatureCollection, Point
from pandas import DataFrame, Series
from pydantic import BaseModel
from s3path import S3Path
from turfpy.measurement import center


def list_to_dataframe[T: BaseModel](object_iterable: Iterable[T]) -> DataFrame:
    """Coerces a list of Pydantic models to a pandas dataframe."""
    return DataFrame([object_row.model_dump() for object_row in object_iterable])


def dataframe_to_list[A](dataframe: DataFrame, cls: type[A]) -> list[A]:
    """Coerces a pandas dataframe into a list of Pydantic models."""
    instance_list: list[A] = []
    for _, row in dataframe.iterrows():
        instance = cls(**row.to_dict())
        instance_list.append(instance)
    return instance_list


namespace_uuid = UUID("13db1bb5-27ac-4bf7-8186-1043347c4247")


def name_to_uuid(name: str) -> UUID:
    """Produce consistent UUIDs for data idempotency."""
    return uuid5(namespace_uuid, name.strip().lower())


def uuid_from_s3_object(path: S3Path) -> str:
    """Compute the UUID of an S3 object given the S3Path to that object."""
    return str(name_to_uuid(path.read_bytes().hex()))


def get_center_of_points(points: list[Point] | Series) -> Point:  # type:ignore[no-any-unimported]
    """Get the center point of a list of geojson geometry points."""
    feature_point_list = [Feature(geometry=point) for point in points]
    return center(FeatureCollection(feature_point_list))["geometry"]


def create_predicate(template: str) -> Callable:
    """Create a function to delay evaluation of a f-string template.

    Create a function that takes `context` as input. This will be evaluated during
    `load_input` and that value of `context` will be within scope.

    Do not provide an f-string as input, as that will lead to immediate formatting. Instead
    provide a regular string with the same formatting syntax as an f-string.

    Example:
        >>> predicate = create_predicate("id='{context.partition_key}'")
        >>> lambda context: "id='{context.partition_key}'".format(context=context)

        Deferring evaluation to within the `load_input` scope results in a predicate clause
        of `"WHERE id='<context.partition_key value>'"`

    Returns:
        - Function that returns an f-string version of the input template, with the
    local context in scope.
    """

    def deferred_string_format(context: InputContext) -> str:
        """Evaluate a template string with the provided context value."""
        return template.format(context=context)

    return deferred_string_format


def transport_params(s3: S3Resource) -> dict:  # pragma: no cover
    """Create the transport_params inputs.

    Inteneded usage is func(inputs,**transport_params(s3))
    """
    return {"transport_params": {"client": s3.get_client()}}


def convert_uri_to_url(uri: str, endpoint_url: str | None) -> str:
    """Convert a URI to a URL."""
    if endpoint_url is None:
        message = "endpoint_url must be provided"
        raise ValueError(message)
    s3_path = S3Path.from_uri(uri)
    bucket = s3_path.bucket
    key = s3_path.key
    if endpoint_url and "amazonaws" in endpoint_url:
        service = "s3"
        region = ""
        if endpoint_url and "us-gov" in endpoint_url:
            pattern = r"s3(\.us-gov-[a-z0-9-]+)\.amazonaws\.com"
            match = re.search(pattern, endpoint_url)
            if match is not None:
                region = f"{match.group(1)}"
        url = f"https://{bucket}.{service}{region}.amazonaws.com/{key}"
    else:
        url = f"{endpoint_url}/{bucket}/{key}"
    return url
