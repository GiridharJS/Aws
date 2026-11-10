import boto3
import pytest
from moto import mock_aws
from src.S3ToDynamo import lambda_handler, parse_log_content


@mock_aws
def test_lambda1_valid_file():
    # Setup S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    # Setup DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="LogsTable",
        KeySchema=[{"AttributeName": "FileId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "FileId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )

    # Upload test log file
    content = "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating"
    s3.put_object(Bucket=bucket, Key="test.log", Body=content)

    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": "test.log"}
            }
        }]
    }

    result = lambda_handler(event, None)

    assert result["status"] == "success"
    assert result["record_count"] == 1