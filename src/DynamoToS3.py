import boto3
import csv
import io
from botocore.exceptions import ClientError, BotoCoreError

s3 = boto3.client('s3')

"""In this Module, The json data from the DynamoDb is Stored in list for future Transformation."""


def process_record(record):
    try:
        if record.get('eventName') != 'INSERT':
            return None

        new_image = record['dynamodb']['NewImage']

        file_id = new_image['FileId']['S']
        data = new_image['Data']['L']

        items = []
        for item in data:
            obj = {}
            for k, v in item['M'].items():
                obj[k] = list(v.values())[0]
            items.append(obj)

        file_name = f"output/{file_id}.csv"
        return file_name, items

    except KeyError as e:
        raise ValueError(f"Missing Image details in DynamoDB Stream record: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"Unexpected processing error: {str(e)}")
    

""" In this Module, the Data Stored in List is converted to CSV format and Stored in the S3->output bucket"""

def upload_to_s3(bucket, file_name, items):
    try:
        if not items:
            print(f"No data to upload for {file_name}")
            return

        csv_buffer = io.StringIO(newline='')

        headers = items[0].keys()
        writer = csv.DictWriter(csv_buffer, fieldnames=headers)

        writer.writeheader()
        writer.writerows(items)

        s3.put_object(
            Bucket=bucket,
            Key=file_name,
            Body=csv_buffer.getvalue()
        )

    except ClientError as e:
        raise RuntimeError(f"S3 ClientError: {e.response['Error']['Code']}")

    except BotoCoreError as e:
        raise RuntimeError(f"S3 BotoCoreError: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"Unexpected S3 upload error: {str(e)}")


"""This is Main Handler.This were the Lambda 2 get's started."""


def lambda_handler(event, context):
    results = []

    #  Validate event structure FIRST
    records = event.get("Records")
    if not isinstance(records, list):
        return {
            "statusCode": 400,
            "error": "Invalid event structure: 'Records' must be a list"
        }

    try:
        for record in records:
            try:
                processed = process_record(record)

                # Skip non-INSERT events
                if processed is None:
                    continue

                file_name, items = processed

                upload_to_s3(
                    bucket="my-output-bucket-giridhar",
                    file_name=file_name,
                    items=items
                )

                results.append({
                    "file_name": file_name,
                    "rows": len(items),
                    "status": "success"
                })

            # 🔹 Specific known errors
            except ValueError as e:
                print(f"Validation error: {str(e)}")
                results.append({
                    "status": "error",
                    "type": "validation",
                    "message": str(e)
                })

            except RuntimeError as e:
                print(f"Processing error: {str(e)}")
                results.append({
                    "status": "error",
                    "type": "processing",
                    "message": str(e)
                })

            # Catch unexpected per-record errors
            except Exception as e:
                print(f"Unexpected record error: {str(e)}")
                results.append({
                    "status": "error",
                    "type": "unknown",
                    "message": str(e)
                })

        return {
            "statusCode": 200,
            "processed": results
        }

    # Top-level critical failure
    except Exception as e:
        return {
            "statusCode": 500,
            "error": f"Critical Lambda failure: {str(e)}"
        }