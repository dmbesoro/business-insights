def process_report(report_id: str) -> None:
    \"\"\"Shared processing entry point.

    Keep extraction, classification and persistence here (or in modules called
    from here), not inside the AWS Lambda handler. This makes the pipeline
    independently testable.
    \"\"\"
    raise NotImplementedError("Implement the report pipeline next.")
