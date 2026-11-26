from app.processing.service import process_report


def handler(event, context):
    \"\"\"AWS Lambda SQS event handler; delegate business logic to service.\"\"\"
    failures = []
    for record in event.get("Records", []):
        try:
            import json
            message = json.loads(record["body"])
            process_report(str(message["report_id"]))
        except Exception:
            # SQS partial batch response allows only failed messages to retry.
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
