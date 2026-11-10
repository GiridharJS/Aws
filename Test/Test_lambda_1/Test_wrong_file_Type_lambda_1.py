import boto3
import pytest
from moto import mock_aws
from src.S3ToDynamo import lambda_handler, parse_log_content
from botocore.exceptions import ClientError, BotoCoreError

"""Verifing that the system successfully rejects invalid file extensions."""
#   Wrong file type
@mock_aws
def test_lambda1_invalid_file_type():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    s3.put_object(Bucket=bucket, Key="test.txt", Body="01012025 10:00:00 123 INFO App Started")
    
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="LogsTable",
        KeySchema=[
            {"AttributeName": "FileId", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "FileId", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": "test.txt"}
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["status"] == "error"


"""Verifing whether the empty files are rejected correctly."""
#  Empty file
@mock_aws
def test_lambda1_empty_file():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="LogsTable",
        KeySchema=[{"AttributeName": "FileId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "FileId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )

    s3.put_object(Bucket=bucket, Key="empty.log", Body="")

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": "empty.log"}
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["status"] =="error"
    assert result["record_count"] == 0

""" TestCase for Invalid event input"""

def test_invalid_event_structure():
    result = lambda_handler({}, None)

    assert result["status"] == "error"
    assert "Invalid event structure" in result["error"]


