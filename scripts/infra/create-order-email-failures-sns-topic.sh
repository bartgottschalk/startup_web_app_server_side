#!/bin/bash

##############################################################################
# Create SNS Topic for Order Email Failure Alerts
#
# This script creates:
# - SNS topic for order email failure notifications
# - Email subscription for alerts
#
# Purpose:
# When order creation succeeds but confirmation email fails to send, this
# SNS topic will receive an alert via CloudWatch Alarm. This ensures the
# support team is immediately notified when customers complete checkout
# but don't receive their confirmation email.
#
# Alert Scenario:
# 1. Customer completes Stripe checkout (payment successful)
# 2. Order saved to database successfully
# 3. Email template lookup, formatting, or SMTP send fails
# 4. Orderemailfailure record created in database
# 5. CloudWatch Metric Filter detects log entry
# 6. CloudWatch Alarm triggers
# 7. SNS sends email notification to support team
#
# Prerequisites:
# - AWS CLI configured with credentials
# - Orderemailfailure model deployed (HIGH-004 implementation)
# - CloudWatch Logs for ECS service enabled
#
# Cost: ~$0.50/month (SNS free tier covers first 1,000 emails/month)
#
# Usage: ./scripts/infra/create-sns-topic.sh <your-email@domain.com>
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create SNS Topic - Order Email Failures${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for email argument
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Email address required${NC}"
    echo -e "${YELLOW}Usage: $0 <your-email@domain.com>${NC}"
    echo ""
    echo -e "${YELLOW}This email will receive alerts when order emails fail to send.${NC}"
    exit 1
fi

ALERT_EMAIL="$1"
echo -e "${GREEN}Alert email: ${ALERT_EMAIL}${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Set default region if not in env file
AWS_REGION=${AWS_REGION:-us-east-1}

# Check if SNS topic already exists
if [ -n "${SNS_TOPIC_ORDER_EMAIL_FAILURES:-}" ]; then
    echo -e "${YELLOW}Checking if SNS topic exists...${NC}"

    # Try to get topic attributes to verify it exists
    TOPIC_EXISTS=$(aws sns get-topic-attributes \
        --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
        --region "${AWS_REGION}" \
        --query 'Attributes.TopicArn' \
        --output text 2>/dev/null || echo "")

    if [ -n "$TOPIC_EXISTS" ]; then
        echo -e "${GREEN}✓ SNS topic already exists: ${SNS_TOPIC_ORDER_EMAIL_FAILURES}${NC}"
        echo ""

        # Check if email is already subscribed
        SUBSCRIPTIONS=$(aws sns list-subscriptions-by-topic \
            --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
            --region "${AWS_REGION}" \
            --query "Subscriptions[?Endpoint=='${ALERT_EMAIL}'].SubscriptionArn" \
            --output text)

        if [ -n "$SUBSCRIPTIONS" ] && [ "$SUBSCRIPTIONS" != "None" ]; then
            echo -e "${GREEN}✓ Email ${ALERT_EMAIL} is already subscribed${NC}"
        else
            echo -e "${YELLOW}Email ${ALERT_EMAIL} is not subscribed. Adding subscription...${NC}"
            aws sns subscribe \
                --topic-arn "${SNS_TOPIC_ORDER_EMAIL_FAILURES}" \
                --protocol email \
                --notification-endpoint "${ALERT_EMAIL}" \
                --region "${AWS_REGION}" > /dev/null
            echo -e "${GREEN}✓ Subscription created. Check ${ALERT_EMAIL} to confirm.${NC}"
        fi

        exit 0
    else
        echo -e "${YELLOW}SNS topic ARN in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will create an SNS topic for order email failure alerts${NC}"
echo ""
echo -e "${YELLOW}Alert Configuration:${NC}"
echo -e "  Topic Name:             ${PROJECT_NAME}-order-email-failures"
echo -e "  Notification Email:     ${ALERT_EMAIL}"
echo -e "  Alert Trigger:          CloudWatch Alarm (configured separately)"
echo ""
echo -e "${YELLOW}Alert Scenarios:${NC}"
echo -e "  - Email template not found in database"
echo -e "  - Email body formatting error"
echo -e "  - SMTP server connection failure"
echo -e "  - Email sending timeout or error"
echo ""
echo -e "${YELLOW}Cost Impact: ~\$0.50/month (free tier: 1,000 emails/month)${NC}"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Create SNS Topic
echo ""
echo -e "${YELLOW}Step 1: Creating SNS topic...${NC}"

TOPIC_ARN=$(aws sns create-topic \
    --name "${PROJECT_NAME}-order-email-failures" \
    --region "${AWS_REGION}" \
    --tags Key=Name,Value="${PROJECT_NAME}-order-email-failures" Key=Environment,Value="${ENVIRONMENT}" Key=Application,Value=StartupWebApp Key=ManagedBy,Value=InfrastructureAsCode Key=AlertType,Value=OrderEmailFailure \
    --output text \
    --query 'TopicArn')

echo -e "${GREEN}✓ SNS topic created${NC}"
echo -e "    ARN: ${TOPIC_ARN}"

# Step 2: Subscribe email to SNS topic
echo ""
echo -e "${YELLOW}Step 2: Subscribing email to SNS topic...${NC}"

SUBSCRIPTION_ARN=$(aws sns subscribe \
    --topic-arn "${TOPIC_ARN}" \
    --protocol email \
    --notification-endpoint "${ALERT_EMAIL}" \
    --region "${AWS_REGION}" \
    --output text \
    --query 'SubscriptionArn')

echo -e "${GREEN}✓ Email subscription created${NC}"
echo -e "    Endpoint: ${ALERT_EMAIL}"
echo -e "    Status:   Pending confirmation"

# Step 3: Update aws-resources.env
echo ""
echo -e "${YELLOW}Step 3: Updating aws-resources.env...${NC}"

# Check if variable exists, add or update
if grep -q "^SNS_TOPIC_ORDER_EMAIL_FAILURES=" "$ENV_FILE"; then
    # Update existing line (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak "s|^SNS_TOPIC_ORDER_EMAIL_FAILURES=.*|SNS_TOPIC_ORDER_EMAIL_FAILURES=\"${TOPIC_ARN}\"|" "$ENV_FILE"
    else
        sed -i.bak "s|^SNS_TOPIC_ORDER_EMAIL_FAILURES=.*|SNS_TOPIC_ORDER_EMAIL_FAILURES=\"${TOPIC_ARN}\"|" "$ENV_FILE"
    fi
else
    # Add new variable
    echo "" >> "$ENV_FILE"
    echo "# Order Email Failure Alerts (HIGH-004)" >> "$ENV_FILE"
    echo "SNS_TOPIC_ORDER_EMAIL_FAILURES=\"${TOPIC_ARN}\"" >> "$ENV_FILE"
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SNS Topic Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Topic Name:             ${PROJECT_NAME}-order-email-failures"
echo -e "  Topic ARN:              ${TOPIC_ARN}"
echo -e "  Notification Email:     ${ALERT_EMAIL}"
echo -e "  Subscription Status:    Pending confirmation"
echo ""
echo -e "${YELLOW}⚠️  ACTION REQUIRED: Confirm Email Subscription${NC}"
echo -e "${YELLOW}1. Check your inbox: ${ALERT_EMAIL}${NC}"
echo -e "${YELLOW}2. Look for email from: AWS Notifications <no-reply@sns.amazonaws.com>${NC}"
echo -e "${YELLOW}3. Click the 'Confirm subscription' link${NC}"
echo ""
echo -e "${GREEN}How It Works:${NC}"
echo -e "  1. Order created successfully, customer payment processed"
echo -e "  2. Email send fails (template, formatting, SMTP error)"
echo -e "  3. Application logs: [ORDER_EMAIL_FAILURE] phase=X order=Y"
echo -e "  4. Orderemailfailure record created in database"
echo -e "  5. CloudWatch Metric Filter detects log pattern"
echo -e "  6. CloudWatch Alarm evaluates metric"
echo -e "  7. SNS sends notification to ${ALERT_EMAIL}"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  List subscriptions:     aws sns list-subscriptions-by-topic --topic-arn ${TOPIC_ARN}"
echo -e "  Test notification:      aws sns publish --topic-arn ${TOPIC_ARN} --message 'Test message'"
echo -e "  View topic attributes:  aws sns get-topic-attributes --topic-arn ${TOPIC_ARN}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Confirm email subscription (check ${ALERT_EMAIL})"
echo -e "  2. Create CloudWatch Alarm: ./scripts/infra/create-order-email-failure-alarm.sh"
echo ""
echo -e "${YELLOW}Note: SNS topic is ready but won't send alerts until CloudWatch Alarm is configured.${NC}"
echo ""
