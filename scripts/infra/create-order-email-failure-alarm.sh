#!/bin/bash

##############################################################################
# Create CloudWatch Alarm for Order Email Failures
#
# This script creates:
# - CloudWatch Log Metric Filter (detects [ORDER_EMAIL_FAILURE] log pattern)
# - CloudWatch Alarm (triggers when metric > 0)
# - Alarm action (sends notification to SNS topic)
#
# Purpose:
# Monitor application logs for order email delivery failures and alert
# the support team immediately. When a customer completes checkout but
# doesn't receive their confirmation email, this alarm ensures the issue
# is detected and addressed promptly.
#
# How It Works:
# 1. Application logs email failure: [ORDER_EMAIL_FAILURE] phase=X order=Y
# 2. CloudWatch Metric Filter matches log pattern
# 3. Metric "OrderEmailFailures" is incremented
# 4. Alarm evaluates metric every 1 minute
# 5. If metric > 0 in any 1-minute period → ALARM state
# 6. SNS sends notification email to support team
#
# Alert Response:
# When you receive an alert:
# 1. Check Orderemailfailure table in database for details
# 2. Verify customer's order was created successfully
# 3. Manually send confirmation email to customer
# 4. Investigate root cause (template, SMTP, network issue)
# 5. Mark Orderemailfailure record as resolved
#
# Prerequisites:
# - SNS topic created (run create-sns-topic-order-email-failures.sh)
# - ECS service logs enabled (ECS_SERVICE_LOG_GROUP in aws-resources.env)
# - Orderemailfailure model deployed (HIGH-004 implementation)
#
# Cost: ~$0.10/month (CloudWatch alarm + metric filter)
#
# Usage: ./scripts/infra/create-order-email-failure-alarm.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"

# Alarm configuration
ALARM_NAME="${PROJECT_NAME}-order-email-failures"
METRIC_NAME="OrderEmailFailures"
METRIC_NAMESPACE="StartupWebApp/Order"
FILTER_NAME="${PROJECT_NAME}-order-email-failure-filter"
FILTER_PATTERN='"[ORDER_EMAIL_FAILURE]"'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create Order Email Failure Alarm${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
echo -e "${YELLOW}Verifying prerequisites...${NC}"

if [ -z "${SNS_TOPIC_ORDER_EMAIL_FAILURES:-}" ]; then
    echo -e "${RED}Error: SNS_TOPIC_ORDER_EMAIL_FAILURES not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-sns-topic-order-email-failures.sh <email>${NC}"
    exit 1
fi

if [ -z "${ECS_SERVICE_LOG_GROUP:-}" ]; then
    echo -e "${RED}Error: ECS_SERVICE_LOG_GROUP not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please ensure ECS service is deployed with CloudWatch logging enabled${NC}"
    exit 1
fi

# Verify SNS topic exists
TOPIC_EXISTS=$(aws sns get-topic-attributes \
    --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --region "${AWS_REGION}" \
    --query 'Attributes.TopicArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$TOPIC_EXISTS" ]; then
    echo -e "${RED}Error: SNS topic not found in AWS${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-sns-topic-order-email-failures.sh <email>${NC}"
    exit 1
fi

# Verify log group exists
LOG_GROUP_EXISTS=$(aws logs describe-log-groups \
    --log-group-name-prefix "${ECS_SERVICE_LOG_GROUP}" \
    --region "${AWS_REGION}" \
    --query "logGroups[?logGroupName=='${ECS_SERVICE_LOG_GROUP}'].logGroupName" \
    --output text 2>/dev/null || echo "")

if [ -z "$LOG_GROUP_EXISTS" ]; then
    echo -e "${RED}Error: CloudWatch log group ${ECS_SERVICE_LOG_GROUP} not found${NC}"
    echo -e "${YELLOW}Please ensure ECS service is deployed and logging to CloudWatch${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites verified${NC}"
echo ""

# Check if alarm already exists
EXISTING_ALARM=$(aws cloudwatch describe-alarms \
    --alarm-names "${ALARM_NAME}" \
    --region "${AWS_REGION}" \
    --query 'MetricAlarms[0].AlarmName' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_ALARM" ] && [ "$EXISTING_ALARM" != "None" ]; then
    echo -e "${GREEN}✓ CloudWatch alarm already exists: ${ALARM_NAME}${NC}"
    echo ""

    # Show current configuration
    ALARM_CONFIG=$(aws cloudwatch describe-alarms \
        --alarm-names "${ALARM_NAME}" \
        --region "${AWS_REGION}" \
        --query 'MetricAlarms[0].{State: StateValue, Metric: MetricName, Threshold: Threshold}' \
        --output json)

    ALARM_STATE=$(echo "$ALARM_CONFIG" | jq -r '.State')
    CURRENT_THRESHOLD=$(echo "$ALARM_CONFIG" | jq -r '.Threshold')

    echo -e "  Current State:          ${ALARM_STATE}"
    echo -e "  Threshold:              ${CURRENT_THRESHOLD}"
    echo -e "  SNS Topic:              ${SNS_TOPIC_ORDER_EMAIL_FAILURES}"
    echo ""
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-order-email-failure-alarm.sh first${NC}"
    exit 0
fi

echo -e "${YELLOW}This will create a CloudWatch alarm for order email failures${NC}"
echo ""
echo -e "${YELLOW}Alarm Configuration:${NC}"
echo -e "  Alarm Name:             ${ALARM_NAME}"
echo -e "  Log Group:              ${ECS_SERVICE_LOG_GROUP}"
echo -e "  Filter Pattern:         ${FILTER_PATTERN}"
echo -e "  Metric Name:            ${METRIC_NAME}"
echo -e "  Metric Namespace:       ${METRIC_NAMESPACE}"
echo -e "  Evaluation Period:      1 minute"
echo -e "  Threshold:              > 0 failures"
echo -e "  SNS Topic:              ${SNS_TOPIC_ORDER_EMAIL_FAILURES}"
echo ""
echo -e "${YELLOW}Alert Trigger:${NC}"
echo -e "  When application logs contain: [ORDER_EMAIL_FAILURE]"
echo ""
echo -e "${YELLOW}Example Log Entry:${NC}"
echo -e "  [ORDER_EMAIL_FAILURE] phase=smtp_send order=ABC123 customer=user@example.com error=Connection timeout"
echo ""
echo -e "${YELLOW}Cost Impact: ~\$0.10/month (CloudWatch alarm + metric)${NC}"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Create Metric Filter
echo ""
echo -e "${YELLOW}Step 1: Creating CloudWatch Log Metric Filter...${NC}"

# Check if metric filter already exists
EXISTING_FILTER=$(aws logs describe-metric-filters \
    --log-group-name "${ECS_SERVICE_LOG_GROUP}" \
    --filter-name-prefix "${FILTER_NAME}" \
    --region "${AWS_REGION}" \
    --query "metricFilters[?filterName=='${FILTER_NAME}'].filterName" \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_FILTER" ] && [ "$EXISTING_FILTER" != "None" ]; then
    echo -e "${GREEN}✓ Metric filter already exists: ${FILTER_NAME}${NC}"
else
    aws logs put-metric-filter \
        --log-group-name "${ECS_SERVICE_LOG_GROUP}" \
        --filter-name "${FILTER_NAME}" \
        --filter-pattern "${FILTER_PATTERN}" \
        --metric-transformations \
            metricName="${METRIC_NAME}",\
metricNamespace="${METRIC_NAMESPACE}",\
metricValue=1,\
defaultValue=0 \
        --region "${AWS_REGION}"

    echo -e "${GREEN}✓ Metric filter created${NC}"
fi

echo -e "    Log Group:              ${ECS_SERVICE_LOG_GROUP}"
echo -e "    Filter Name:            ${FILTER_NAME}"
echo -e "    Filter Pattern:         ${FILTER_PATTERN}"
echo -e "    Metric Name:            ${METRIC_NAME}"
echo -e "    Metric Namespace:       ${METRIC_NAMESPACE}"

# Step 2: Create CloudWatch Alarm
echo ""
echo -e "${YELLOW}Step 2: Creating CloudWatch Alarm...${NC}"

aws cloudwatch put-metric-alarm \
    --alarm-name "${ALARM_NAME}" \
    --alarm-description "Alert when order confirmation emails fail to send. Customer has paid but didn't receive confirmation email." \
    --metric-name "${METRIC_NAME}" \
    --namespace "${METRIC_NAMESPACE}" \
    --statistic Sum \
    --period 60 \
    --evaluation-periods 1 \
    --threshold 0 \
    --comparison-operator GreaterThanThreshold \
    --treat-missing-data notBreaching \
    --alarm-actions "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
    --tags Key=Name,Value="${ALARM_NAME}" Key=Environment,Value="${ENVIRONMENT}" Key=Application,Value=StartupWebApp Key=ManagedBy,Value=InfrastructureAsCode Key=AlertType,Value=OrderEmailFailure \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ CloudWatch alarm created${NC}"
echo -e "    Alarm Name:             ${ALARM_NAME}"
echo -e "    Evaluation:             Every 1 minute"
echo -e "    Threshold:              > 0 failures"
echo -e "    Action:                 Send SNS notification"

# Step 3: Update aws-resources.env
echo ""
echo -e "${YELLOW}Step 3: Updating aws-resources.env...${NC}"

# Check if variable exists, add or update
if grep -q "^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
    # Update existing line (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak "s|^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=.*|CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=\"${ALARM_NAME}\"|" "$ENV_FILE"
    else
        sed -i.bak "s|^CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=.*|CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=\"${ALARM_NAME}\"|" "$ENV_FILE"
    fi
else
    # Add new variable (if SNS topic line exists, add after it)
    if grep -q "^SNS_TOPIC_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i .bak "/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/a\\
CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=\"${ALARM_NAME}\"
" "$ENV_FILE"
        else
            sed -i.bak "/^SNS_TOPIC_ORDER_EMAIL_FAILURES=/a CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=\"${ALARM_NAME}\"" "$ENV_FILE"
        fi
    else
        # SNS topic line doesn't exist, add at end
        echo "CLOUDWATCH_ALARM_ORDER_EMAIL_FAILURES=\"${ALARM_NAME}\"" >> "$ENV_FILE"
    fi
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Step 4: Verify alarm is active
echo ""
echo -e "${YELLOW}Step 4: Verifying alarm status...${NC}"

ALARM_STATE=$(aws cloudwatch describe-alarms \
    --alarm-names "${ALARM_NAME}" \
    --region "${AWS_REGION}" \
    --query 'MetricAlarms[0].StateValue' \
    --output text)

echo -e "  Alarm State: ${ALARM_STATE}"

if [ "$ALARM_STATE" == "INSUFFICIENT_DATA" ]; then
    echo -e "${GREEN}✓ Alarm is active (INSUFFICIENT_DATA is normal for new alarms)${NC}"
elif [ "$ALARM_STATE" == "OK" ]; then
    echo -e "${GREEN}✓ Alarm is active and OK (no failures detected)${NC}"
elif [ "$ALARM_STATE" == "ALARM" ]; then
    echo -e "${RED}⚠ Alarm is in ALARM state (email failures detected!)${NC}"
else
    echo -e "${YELLOW}⚠ Alarm state: ${ALARM_STATE}${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CloudWatch Alarm Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Alarm Name:             ${ALARM_NAME}"
echo -e "  Metric Filter:          ${FILTER_NAME}"
echo -e "  Log Group:              ${ECS_SERVICE_LOG_GROUP}"
echo -e "  Filter Pattern:         ${FILTER_PATTERN}"
echo -e "  Metric:                 ${METRIC_NAMESPACE}/${METRIC_NAME}"
echo -e "  Current State:          ${ALARM_STATE}"
echo -e "  SNS Topic:              ${SNS_TOPIC_ORDER_EMAIL_FAILURES}"
echo ""
echo -e "${GREEN}How It Works:${NC}"
echo -e "  1. Application logs: [ORDER_EMAIL_FAILURE] phase=X order=Y customer=Z"
echo -e "  2. Metric filter detects pattern and increments ${METRIC_NAME}"
echo -e "  3. Alarm evaluates metric every 1 minute"
echo -e "  4. If metric > 0 → SNS sends email notification"
echo -e "  5. Support team receives alert with details"
echo ""
echo -e "${GREEN}When You Receive an Alert:${NC}"
echo -e "  1. Connect to production database"
echo -e "  2. Query: SELECT * FROM order_order_email_failure WHERE resolved = false ORDER BY created_date_time DESC;"
echo -e "  3. Verify customer's order exists and payment processed"
echo -e "  4. Manually send confirmation email to customer"
echo -e "  5. Investigate root cause (check error_message field)"
echo -e "  6. Mark as resolved: UPDATE order_order_email_failure SET resolved=true, resolved_date_time=NOW(), resolved_by='Your Name' WHERE id=X;"
echo ""
echo -e "${GREEN}Test the Alarm:${NC}"
echo -e "  1. Deploy HIGH-004 implementation to production"
echo -e "  2. Temporarily break email configuration (rename template in DB)"
echo -e "  3. Complete a test checkout"
echo -e "  4. Wait 1-2 minutes for alarm to trigger"
echo -e "  5. Check email for SNS notification"
echo -e "  6. Restore email configuration"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  View alarm status:      aws cloudwatch describe-alarms --alarm-names ${ALARM_NAME}"
echo -e "  View alarm history:     aws cloudwatch describe-alarm-history --alarm-name ${ALARM_NAME} --max-records 10"
echo -e "  View metric data:       aws cloudwatch get-metric-statistics --namespace ${METRIC_NAMESPACE} --metric-name ${METRIC_NAME} --start-time \$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time \$(date -u +%Y-%m-%dT%H:%M:%S) --period 60 --statistics Sum"
echo -e "  Test SNS notification:  aws sns publish --topic-arn ${SNS_TOPIC_ORDER_EMAIL_FAILURES} --message 'Test alert'"
echo ""
echo -e "${YELLOW}Note: Alarm is active and monitoring. You'll receive email alerts when order emails fail.${NC}"
echo ""
echo -e "${GREEN}HIGH-004 Monitoring Complete! ✓${NC}"
echo -e "  ✓ SNS Topic created"
echo -e "  ✓ CloudWatch Metric Filter created"
echo -e "  ✓ CloudWatch Alarm created"
echo -e "  → Ready for production deployment"
echo ""
