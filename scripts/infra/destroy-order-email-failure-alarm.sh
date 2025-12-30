#!/bin/bash

##############################################################################
# Destroy CloudWatch Alarm for Order Email Failures
#
# This script deletes:
# - CloudWatch Alarm
# - CloudWatch Log Metric Filter
#
# WARNING: After running this script:
# - No alerts will be sent when order emails fail
# - Metric data will stop being collected
# - Support team will not be notified of email delivery issues
# - SNS topic will remain (run destroy-sns-topic-order-email-failures.sh to remove)
#
# Usage: ./scripts/infra/destroy-order-email-failure-alarm.sh
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

# Alarm configuration (must match create script)
ALARM_NAME="${PROJECT_NAME}-order-email-failures"
FILTER_NAME="${PROJECT_NAME}-order-email-failure-filter"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroy Order Email Failure Alarm${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if alarm exists in env file
if [ -z "${CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES:-}" ]; then
    echo -e "${YELLOW}No alarm name found in aws-resources.env${NC}"
    echo -e "${YELLOW}Checking for alarm in AWS anyway...${NC}"
fi

# Check if alarm exists in AWS
ALARM_EXISTS=$(aws cloudwatch describe-alarms \
    --alarm-names "${ALARM_NAME}" \
    --region "${AWS_REGION}" \
    --query 'MetricAlarms[0].AlarmName' \
    --output text 2>/dev/null || echo "")

if [ -z "$ALARM_EXISTS" ] || [ "$ALARM_EXISTS" == "None" ]; then
    echo -e "${YELLOW}Alarm not found in AWS${NC}"

    # Check for metric filter
    if [ -n "${ECS_SERVICE_LOG_GROUP:-}" ]; then
        FILTER_EXISTS=$(aws logs describe-metric-filters \
            --log-group-name "${ECS_SERVICE_LOG_GROUP}" \
            --filter-name-prefix "${FILTER_NAME}" \
            --region "${AWS_REGION}" \
            --query "metricFilters[?filterName=='${FILTER_NAME}'].filterName" \
            --output text 2>/dev/null || echo "")

        if [ -z "$FILTER_EXISTS" ] || [ "$FILTER_EXISTS" == "None" ]; then
            echo -e "${YELLOW}Metric filter not found in AWS${NC}"
            echo -e "${GREEN}Nothing to delete.${NC}"

            # Clear env file if needed
            if grep -q "^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
                echo -e "${YELLOW}Clearing env file...${NC}"
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i .bak '/^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=/d' "$ENV_FILE"
                else
                    sed -i.bak '/^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=/d' "$ENV_FILE"
                fi
                rm -f "${ENV_FILE}.bak"
                echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
            fi

            exit 0
        fi
    else
        echo -e "${GREEN}Nothing to delete.${NC}"
        exit 0
    fi
fi

# Get alarm details
if [ -n "$ALARM_EXISTS" ]; then
    ALARM_CONFIG=$(aws cloudwatch describe-alarms \
        --alarm-names "${ALARM_NAME}" \
        --region "${AWS_REGION}" \
        --query 'MetricAlarms[0].{State: StateValue, Metric: MetricName, Namespace: Namespace, SNS: AlarmActions[0]}' \
        --output json)

    ALARM_STATE=$(echo "$ALARM_CONFIG" | jq -r '.State')
    METRIC_NAME=$(echo "$ALARM_CONFIG" | jq -r '.Metric')
    METRIC_NAMESPACE=$(echo "$ALARM_CONFIG" | jq -r '.Namespace')
    SNS_TOPIC=$(echo "$ALARM_CONFIG" | jq -r '.SNS')
fi

# Confirm destruction
echo -e "${RED}WARNING: This will delete the CloudWatch alarm for order email failures!${NC}"
echo -e "${RED}No alerts will be sent when order emails fail to deliver.${NC}"
echo ""
echo -e "${YELLOW}Resources to be deleted:${NC}"
if [ -n "$ALARM_EXISTS" ]; then
    echo -e "  Alarm Name:           ${ALARM_NAME}"
    echo -e "  Current State:        ${ALARM_STATE}"
    echo -e "  Metric:               ${METRIC_NAMESPACE}/${METRIC_NAME}"
    echo -e "  SNS Topic:            ${SNS_TOPIC}"
fi
if [ -n "${ECS_SERVICE_LOG_GROUP:-}" ]; then
    echo -e "  Metric Filter:        ${FILTER_NAME}"
    echo -e "  Log Group:            ${ECS_SERVICE_LOG_GROUP}"
fi
echo ""
echo -e "${YELLOW}Cost Savings: ~\$0.10/month${NC}"
echo ""

read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Delete CloudWatch Alarm
echo ""
echo -e "${YELLOW}Step 1: Deleting CloudWatch Alarm...${NC}"

if [ -n "$ALARM_EXISTS" ]; then
    aws cloudwatch delete-alarms \
        --alarm-names "${ALARM_NAME}" \
        --region "${AWS_REGION}" 2>/dev/null || true
    echo -e "${GREEN}✓ CloudWatch alarm deleted: ${ALARM_NAME}${NC}"
else
    echo -e "${YELLOW}No alarm found, skipping...${NC}"
fi

# Step 2: Delete Metric Filter
echo ""
echo -e "${YELLOW}Step 2: Deleting CloudWatch Log Metric Filter...${NC}"

if [ -n "${ECS_SERVICE_LOG_GROUP:-}" ]; then
    FILTER_EXISTS=$(aws logs describe-metric-filters \
        --log-group-name "${ECS_SERVICE_LOG_GROUP}" \
        --filter-name-prefix "${FILTER_NAME}" \
        --region "${AWS_REGION}" \
        --query "metricFilters[?filterName=='${FILTER_NAME}'].filterName" \
        --output text 2>/dev/null || echo "")

    if [ -n "$FILTER_EXISTS" ] && [ "$FILTER_EXISTS" != "None" ]; then
        aws logs delete-metric-filter \
            --log-group-name "${ECS_SERVICE_LOG_GROUP}" \
            --filter-name "${FILTER_NAME}" \
            --region "${AWS_REGION}" 2>/dev/null || true
        echo -e "${GREEN}✓ Metric filter deleted: ${FILTER_NAME}${NC}"
    else
        echo -e "${YELLOW}No metric filter found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}No log group found in env file, skipping...${NC}"
fi

# Step 3: Clear environment file
echo ""
echo -e "${YELLOW}Step 3: Clearing aws-resources.env...${NC}"

# Remove alarm variable from env file
if grep -q "^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak '/^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=/d' "$ENV_FILE"
    else
        sed -i.bak '/^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=/d' "$ENV_FILE"
    fi
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
else
    echo -e "${YELLOW}No alarm variable found in env file${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CloudWatch Alarm Destroyed Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Removed:${NC}"
if [ -n "$ALARM_EXISTS" ]; then
    echo -e "  • CloudWatch Alarm: ${ALARM_NAME}"
    echo -e "  • Metric: ${METRIC_NAMESPACE}/${METRIC_NAME}"
fi
echo -e "  • Metric Filter: ${FILTER_NAME}"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  - No alerts will be sent for order email failures"
echo -e "  - Metric data collection has stopped"
echo -e "  - Support team will NOT be notified of email delivery issues"
echo -e "  - SNS topic still exists (run destroy-sns-topic-order-email-failures.sh to remove)"
echo ""
echo -e "${YELLOW}To restore alerts:${NC}"
echo -e "  1. Ensure SNS topic exists (or create: ./scripts/infra/create-sns-topic-order-email-failures.sh <email>)"
echo -e "  2. Run: ./scripts/infra/create-order-email-failure-alarm.sh"
echo ""
