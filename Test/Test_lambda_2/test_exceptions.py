import boto3
import pytest
from moto import mock_aws
from botocore.exceptions import ClientError
from src.DynamoToS3 import lambda_handler

@mock_aws
def test_s3_client_error_moto_only():

    # NOTE: We are NOT creating bucket → this will cause failure

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

    assert result["processed"][0]["status"] == "error"


def test_lambda_invalid_records_type():
    event = {
        "Records": "not-a-list" 
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 400
    