import boto3
import pytest
from moto import mock_aws
from src.DynamoToS3 import lambda_handler,process_record

"""In this Module, the lambda 2 handler is validated based on the Status and Transformed Code."""
@mock_aws
def test_lambda2_valid():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "my-output-bucket-giridhar"
    s3.create_bucket(Bucket=bucket)

    event = {
        "Records": [{
            "eventName": "INSERT",
            "dynamodb": {
                "NewImage": {
                    "FileId": {"S": "file1"},
                    "Data": {
                        "L": [{
                            "M": {
                                "LineId": {"S": "1"},
                                "Level": {"S": "INFO"}
                            }
                        }]
                    }
                }
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["processed"][0]["rows"] == 1

    # Check S3 file
    response = s3.get_object(Bucket=bucket, Key="output/file1.csv")
    content = response["Body"].read().decode()

    assert "INFO" in content


def test_lambda2_skip_non_insert():
    event = {
        "Records": [
            {"eventName": "MODIFY"}
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["processed"] == []


def test_lambda2_empty_records():
    event = {"Records": []}

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["processed"] == []