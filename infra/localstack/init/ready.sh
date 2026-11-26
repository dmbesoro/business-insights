#!/bin/bash
set -euo pipefail
awslocal s3 mb s3://business-insights || true
awslocal sqs create-queue --queue-name report-processing-dlq >/dev/null
DLQ_ARN="$(awslocal sqs get-queue-attributes --queue-url http://localhost:4566/000000000000/report-processing-dlq --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)"
QUEUE_URL="$(awslocal sqs create-queue \
  --queue-name report-processing \
  --query QueueUrl \
  --output text)"

awslocal sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\",\"VisibilityTimeout\":\"60\"}"
echo "LocalStack resources initialized."
