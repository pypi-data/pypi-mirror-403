import pytest
from unittest.mock import Mock, patch
from dagster_aws.s3 import S3Resource
from geojson import Point
from pydantic import BaseModel
from uuid import UUID
from horizon_data_core.helpers import (
    convert_uri_to_url,
    create_predicate,
    dataframe_to_list,
    list_to_dataframe,
    get_center_of_points,
    name_to_uuid,
    uuid_from_s3_object,
)
from pandas import DataFrame
from s3path import S3Path


def test_get_center_of_points() -> None:
    point = {"coordinates": [1.0, 1.0], "type": "Point"}
    assert get_center_of_points([point]) == Point([1.0, 1.0])


mock_region = "us-gov-east-1"
mock_bucket = "bucket"
mock_s3_resource = S3Resource(endpoint_url=f"https://{mock_bucket}.s3.{mock_region}.amazonaws.com")
mock_local_s3_resource = S3Resource(endpoint_url="http://localhost:9000")


def test_convert_uri_to_url() -> None:
    mock_uri = "s3://bucket/data.csv"
    mock_local_uri = "s3://bucket/data.csv"
    assert (
        convert_uri_to_url(mock_uri, mock_s3_resource.endpoint_url)
        == f"https://{mock_bucket}.s3.{mock_region}.amazonaws.com/data.csv"
    )
    assert (
        convert_uri_to_url(mock_local_uri, mock_local_s3_resource.endpoint_url)
        == f"http://localhost:9000/{mock_bucket}/data.csv"
    )
    with pytest.raises(ValueError, match="endpoint_url must be provided"):
        convert_uri_to_url("", None)


def test_deferred_string() -> None:
    deferred = create_predicate("uses {context}")
    assert deferred(context="context_now") == "uses context_now"


def test_dataframe_to_list() -> None:
    generic_dataframe = DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    result = dataframe_to_list(generic_dataframe, dict)
    assert result == [{"A": 1, "B": 4}, {"A": 2, "B": 5}, {"A": 3, "B": 6}]

def test_list_to_dataframe() -> None:
    """Test that list_to_dataframe converts Pydantic models to DataFrame."""
    class TestModel(BaseModel):
        name: str
        value: int
    
    models = [
        TestModel(name="Item 1", value=10),
        TestModel(name="Item 2", value=20),
    ]
    
    result = list_to_dataframe(models)
    
    assert isinstance(result, DataFrame)
    assert len(result) == 2
    assert list(result.columns) == ["name", "value"]
    assert result.iloc[0]["name"] == "Item 1"
    assert result.iloc[0]["value"] == 10
    assert result.iloc[1]["name"] == "Item 2"
    assert result.iloc[1]["value"] == 20

def test_name_to_uuid() -> None:
    """Test that name_to_uuid produces consistent UUIDs."""
    name1 = "Test Entity"
    name2 = "test entity"
    name3 = "  Test Entity  "
    
    uuid1 = name_to_uuid(name1)
    uuid2 = name_to_uuid(name2)
    uuid3 = name_to_uuid(name3)
    
    assert isinstance(uuid1, UUID)
    assert uuid1 == uuid2
    assert uuid1 == uuid3

def test_uuid_from_s3_object() -> None:
    """Test that uuid_from_s3_object computes UUID from S3 object bytes."""
    # Create a mock S3Path
    mock_path = Mock(spec=S3Path)
    mock_path.read_bytes.return_value = b"test content"
    
    # Calculate expected UUID (name_to_uuid of hex of bytes)
    expected_hex = b"test content".hex()
    expected_uuid = name_to_uuid(expected_hex)
    
    result = uuid_from_s3_object(mock_path)
    
    assert isinstance(result, str)
    assert result == str(expected_uuid)
    mock_path.read_bytes.assert_called_once()