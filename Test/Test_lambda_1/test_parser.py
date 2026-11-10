from src.S3ToDynamo import parse_log_content

# Unit test for parser

#Correct Data Testing :
def test_parse_log_content_valid():
    content = "01012025 10:00:00 123 INFO App Started"
    records = parse_log_content(content)

    assert len(records) == 1
    assert records[0]["Level"] == "INFO"

#InCorrect Data Testing :
def test_parse_log_content_invalid():
    content = "bad data"
    records = parse_log_content(content)

    assert len(records) == 0
