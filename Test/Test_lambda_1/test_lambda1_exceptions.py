import boto3
import pytest
from moto import mock_aws
from botocore.exceptions import ClientError
from src.S3ToDynamo import lambda_handler

@mock_aws
def test_s3_failure():

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bucket")

    # DO NOT upload file

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "bucket"},
                "object": {"key": "missing.log"}
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["status"] == "error"
    assert "S3 ClientError while reading file" in result["error"]


@mock_aws
def test_dynamodb_failure():
    s3 = boto3.client("s3", region_name="us-east-1")
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    s3.put_object(Bucket=bucket, Key="test.log", Body="valid log line")

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": "test.log"}
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["status"] == "error"
    assert "DynamoDB ClientError while writing file" in result["error"]