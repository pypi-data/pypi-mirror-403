from horizon_data_core.resources.s3 import S3Bucket
def test_s3_resource() -> None:
    """Test that the S3 resource can be created."""
    s3_resource = S3Bucket(
        s3_bucket="bucket",
        s3_prefix="prefix",
    )
    assert s3_resource.path().as_uri() == "s3://bucket/prefix"
