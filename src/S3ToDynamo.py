import boto3
from botocore.exceptions import ClientError, BotoCoreError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('LogsTable')

""" In this module, the Content or Data  from the S3 Bucket mentioned in the Event section of the Trigger is Decoded."""
# Read file from S3
def read_s3_file(bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')

    except ClientError as e:
        error_code = e.response['Error']['Code']
        raise RuntimeError(f"S3 ClientError while reading file '{key}' from bucket '{bucket}': {error_code}")

    except BotoCoreError as e:
        raise RuntimeError(f"BotoCoreError while accessing S3: {str(e)}")


"""In this Module, the Log data from the log file is processed."""

def parse_log_content(content):
    records = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        try:
            inner = line.strip().split()

            if len(inner) < 5:
                continue

            d = inner[0]

            formatted = d[:2] + "|" + d[2:4] + "|" + d[4:] if len(d) >= 8 else d

            records.append({
                "LineId": str(i + 1),
                "Date": formatted,
                "Time": inner[1],
                "Pid": inner[2],
                "Level": inner[3],
                "Component": inner[4],
                "Content": " ".join(inner[5:])
            })

        except (IndexError, ValueError) as e:
            print(f"Parsing error at line {i+1}: {str(e)}")
            continue

    return records

"""In this Module, the Transformed Data is stored in DynamoDb."""

def write_to_dynamodb(file_id, records):
    try:
        table.put_item(
            Item={
                "FileId": file_id,
                "Data": records
            }
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        raise RuntimeError(f"DynamoDB ClientError while writing file '{file_id}': {error_code}")

    except BotoCoreError as e:
        raise RuntimeError(f"DynamoDB BotoCoreError: {str(e)}")

"""This is main handler.The Lambda get's started from here."""

def lambda_handler(event, context):

    result = {
        "status": "unknown",
        "file": None,
        "record_count": 0,
        "error": None
    }

    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        result["file"] = key

        #  File type validation
        if not key.endswith(".log"):
            raise ValueError(f"Invalid file type '{key}'. Only .log files are allowed.")

        content = read_s3_file(bucket, key)

        if not content.strip():
            raise ValueError("Uploaded file is empty.")

        records = parse_log_content(content)
        result["record_count"] = len(records)

        write_to_dynamodb(key, records)

        result["status"] = "success"

    except KeyError as e:
        result["status"] = "error"
        result["error"] = f"Invalid event structure. Missing key: {str(e)}"

    except ValueError as e:
        result["status"] = "error"
        result["error"] = f"Validation Error: {str(e)}"

    except RuntimeError as e:
        result["status"] = "error"
        result["error"] = str(e)

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error occurred: {str(e)}"

    print("Stored full JSON into DynamoDB")
    return result