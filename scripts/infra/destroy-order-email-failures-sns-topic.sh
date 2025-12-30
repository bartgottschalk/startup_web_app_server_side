#!/bin/bash

##############################################################################
# Destroy SNS Topic for Order Email Failure Alerts
#
# This script deletes:
# - Email subscriptions to the topic
# - SNS topic for order email failures
#
# WARNING: After running this script:
# - No alerts will be sent when order emails fail
# - Support team will not be notified of email delivery issues
# - You must recreate the topic and CloudWatch alarm to restore alerts
#
# Usage: ./scripts/infra/destroy-sns-topic.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroy SNS Topic - Order Email Failures${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if SNS topic exists
if [ -z "${SNS_TOPIC_ORDER_EMAIL_FAILURES:-}" ]; then
    echo -e "${YELLOW}No SNS topic ARN found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to delete.${NC}"
    exit 0
fi

# Verify topic exists in AWS
TOPIC_EXISTS=$(aws sns get-topic-attributes \
    --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --region "${AWS_REGION}" \
    --query 'Attributes.TopicArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$TOPIC_EXISTS" ]; then
    echo -e "${YELLOW}SNS topic ARN in env file but not found in AWS${NC}"
    echo -e "${YELLOW}Clearing env file...${NC}"

    # Clear env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak \
            -e '/^# Order Email Failure Alerts/d' \
            -e '/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/d' \
            "$ENV_FILE"
    else
        sed -i.bak \
            -e '/^# Order Email Failure Alerts/d' \
            -e '/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/d' \
            "$ENV_FILE"
    fi
    rm -f "${ENV_FILE}.bak"

    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
    exit 0
fi

# Get topic details
TOPIC_NAME=$(aws sns get-topic-attributes \
    --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --region "${AWS_REGION}" \
    --query 'Attributes.DisplayName' \
    --output text 2>/dev/null || echo "${PROJECT_NAME}-order-email-failures")

# Get subscription count
SUBSCRIPTIONS=$(aws sns list-subscriptions-by-topic \
    --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --region "${AWS_REGION}" \
    --query 'Subscriptions[*].{Endpoint: Endpoint, Protocol: Protocol}' \
    --output json)

SUBSCRIPTION_COUNT=$(echo "$SUBSCRIPTIONS" | jq '. | length')

# Confirm destruction
echo -e "${RED}WARNING: This will delete the SNS topic for order email failure alerts!${NC}"
echo -e "${RED}No alerts will be sent when order emails fail to deliver.${NC}"
echo ""
echo -e "${YELLOW}Resources to be deleted:${NC}"
echo -e "  Topic Name:       ${TOPIC_NAME}"
echo -e "  Topic ARN:        ${SNS_TOPIC_ORDER_EMAIL_FAILURES}"
echo -e "  Subscriptions:    ${SUBSCRIPTION_COUNT}"
echo ""

if [ "$SUBSCRIPTION_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Email Subscriptions:${NC}"
    echo "$SUBSCRIPTIONS" | jq -r '.[] | "  - \(.Protocol): \(.Endpoint)"'
    echo ""
fi

echo -e "${YELLOW}Cost Savings: ~\$0.50/month${NC}"
echo ""

read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Unsubscribe all email subscriptions
echo ""
echo -e "${YELLOW}Step 1: Unsubscribing email addresses...${NC}"

if [ "$SUBSCRIPTION_COUNT" -gt 0 ]; then
    SUBSCRIPTION_ARNS=$(aws sns list-subscriptions-by-topic \
        --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
        --region "${AWS_REGION}" \
        --query 'Subscriptions[*].SubscriptionArn' \
        --output text)

    for SUB_ARN in $SUBSCRIPTION_ARNS; do
        if [ "$SUB_ARN" != "PendingConfirmation" ] && [ "$SUB_ARN" != "None" ]; then
            aws sns unsubscribe \
                --subscription-arn "$SUB_ARN" \
                --region "${AWS_REGION}" 2>/dev/null || true
            echo -e "${GREEN}✓ Unsubscribed: ${SUB_ARN}${NC}"
        fi
    done

    echo -e "${GREEN}✓ All subscriptions removed${NC}"
else
    echo -e "${YELLOW}No subscriptions to remove${NC}"
fi

# Step 2: Delete SNS Topic
echo ""
echo -e "${YELLOW}Step 2: Deleting SNS topic...${NC}"

aws sns delete-topic \
    --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --region "${AWS_REGION}" 2>/dev/null || true

echo -e "${GREEN}✓ SNS topic deleted${NC}"

# Step 3: Clear environment file
echo ""
echo -e "${YELLOW}Step 3: Clearing aws-resources.env...${NC}"

# Remove SNS topic variable from env file
if grep -q "^SNS_TOPIC_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak \
            -e '/^# Order Email Failure Alerts/d' \
            -e '/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/d' \
            "$ENV_FILE"
    else
        sed -i.bak \
            -e '/^# Order Email Failure Alerts/d' \
            -e '/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/d' \
            "$ENV_FILE"
    fi
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
else
    echo -e "${YELLOW}No SNS topic variable found in env file${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SNS Topic Destroyed Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Removed:${NC}"
echo -e "  • SNS Topic: ${TOPIC_NAME}"
echo -e "  • Subscriptions: ${SUBSCRIPTION_COUNT}"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  - No alerts will be sent for order email failures"
echo -e "  - CloudWatch Alarm (if exists) will now fail to send notifications"
echo -e "  - Support team will NOT be notified of email delivery issues"
echo ""
echo -e "${YELLOW}To restore alerts:${NC}"
echo -e "  1. Run: ./scripts/infra/create-sns-topic.sh <your-email@domain.com>"
echo -e "  2. Confirm email subscription"
echo -e "  3. Run: ./scripts/infra/create-order-email-failure-alarm.sh"
echo ""
