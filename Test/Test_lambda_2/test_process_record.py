import pytest
from src.DynamoToS3 import process_record,lambda_handler

def test_process_record_success():
    record = {
        "eventName": "INSERT",
        "dynamodb": {
            "NewImage": {
                "FileId": {"S": "file1"},
                "Data": {"L": []}
            }
        }
    }

    result = process_record(record)

    assert result[0] == "output/file1.csv"
    assert result[1] == []


def test_lambda_missing_key():

    event = {
        "Records": [{
            "eventName": "INSERT"
        }]
    }

    result = lambda_handler(event, None)

    assert result["processed"][0]["status"] == "error"
    assert result["processed"][0]["type"] == "validation"
    assert result["processed"]