#!/bin/bash

##############################################################################
# Create CloudWatch Monitoring and Alarms for RDS
#
# This script creates:
# - SNS topic for RDS alerts
# - Email subscription
# - CloudWatch alarms (CPU, connections, storage, memory)
# - CloudWatch dashboard
#
# Usage: ./scripts/infra/create-monitoring.sh <your-email@domain.com>
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: RDS instance must be created
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
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating CloudWatch Monitoring${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for email argument
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Email address required${NC}"
    echo -e "${YELLOW}Usage: $0 <your-email@domain.com>${NC}"
    exit 1
fi

ALERT_EMAIL="$1"
echo -e "${GREEN}Alert email: ${ALERT_EMAIL}${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify RDS instance exists
if [ -z "$RDS_INSTANCE_ID" ]; then
    echo -e "${RED}Error: RDS_INSTANCE_ID not found${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-rds.sh first${NC}"
    exit 1
fi

# Check if SNS topic already exists
if [ -n "${SNS_TOPIC_ARN:-}" ]; then
    echo -e "${YELLOW}Monitoring already configured${NC}"
    echo -e "${YELLOW}SNS Topic: ${SNS_TOPIC_ARN}${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-monitoring.sh first${NC}"
    exit 0
fi

# Create SNS topic
echo -e "${YELLOW}Creating SNS topic for RDS alerts...${NC}"
SNS_TOPIC_ARN=$(aws sns create-topic \
    --name "${PROJECT_NAME}-rds-alerts" \
    --tags "Key=Name,Value=${PROJECT_NAME}-rds-alerts" \
           "Key=Environment,Value=${ENVIRONMENT}" \
           "Key=Application,Value=StartupWebApp" \
    --query 'TopicArn' \
    --output text)
echo -e "${GREEN}✓ SNS topic created: ${SNS_TOPIC_ARN}${NC}"

# Subscribe email to topic
echo -e "${YELLOW}Subscribing ${ALERT_EMAIL} to SNS topic...${NC}"
SNS_SUBSCRIPTION_ARN=$(aws sns subscribe \
    --topic-arn "$SNS_TOPIC_ARN" \
    --protocol email \
    --notification-endpoint "$ALERT_EMAIL" \
    --query 'SubscriptionArn' \
    --output text)
echo -e "${GREEN}✓ Email subscription created${NC}"
echo -e "${YELLOW}⚠ Check your email and confirm the subscription!${NC}"

# Create CloudWatch Alarms

# 1. CPU Utilization Alarm
echo -e "${YELLOW}Creating CPU utilization alarm...${NC}"
aws cloudwatch put-metric-alarm \
    --alarm-name "${PROJECT_NAME}-rds-cpu-high" \
    --alarm-description "Alert when RDS CPU exceeds 70%" \
    --metric-name CPUUtilization \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 70 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value="$RDS_INSTANCE_ID" \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --tags "Key=Name,Value=${PROJECT_NAME}-rds-cpu-high" \
           "Key=Environment,Value=${ENVIRONMENT}"
echo -e "${GREEN}✓ CPU alarm created${NC}"

# 2. Database Connections Alarm
echo -e "${YELLOW}Creating database connections alarm...${NC}"
aws cloudwatch put-metric-alarm \
    --alarm-name "${PROJECT_NAME}-rds-connections-high" \
    --alarm-description "Alert when RDS connections exceed 80" \
    --metric-name DatabaseConnections \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value="$RDS_INSTANCE_ID" \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --tags "Key=Name,Value=${PROJECT_NAME}-rds-connections-high" \
           "Key=Environment,Value=${ENVIRONMENT}"
echo -e "${GREEN}✓ Connections alarm created${NC}"

# 3. Free Storage Space Alarm (< 2 GB)
echo -e "${YELLOW}Creating free storage alarm...${NC}"
aws cloudwatch put-metric-alarm \
    --alarm-name "${PROJECT_NAME}-rds-storage-low" \
    --alarm-description "Alert when RDS free storage below 2GB" \
    --metric-name FreeStorageSpace \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 2147483648 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value="$RDS_INSTANCE_ID" \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --tags "Key=Name,Value=${PROJECT_NAME}-rds-storage-low" \
           "Key=Environment,Value=${ENVIRONMENT}"
echo -e "${GREEN}✓ Storage alarm created${NC}"

# 4. Free Memory Alarm (< 500 MB)
echo -e "${YELLOW}Creating free memory alarm...${NC}"
aws cloudwatch put-metric-alarm \
    --alarm-name "${PROJECT_NAME}-rds-memory-low" \
    --alarm-description "Alert when RDS free memory below 500MB" \
    --metric-name FreeableMemory \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 524288000 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value="$RDS_INSTANCE_ID" \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --tags "Key=Name,Value=${PROJECT_NAME}-rds-memory-low" \
           "Key=Environment,Value=${ENVIRONMENT}"
echo -e "${GREEN}✓ Memory alarm created${NC}"

# Create CloudWatch Dashboard
echo -e "${YELLOW}Creating CloudWatch dashboard...${NC}"
DASHBOARD_BODY=$(cat <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "CPUUtilization", {"stat": "Average", "label": "CPU %"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "CPU Utilization",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "DatabaseConnections", {"stat": "Average", "label": "Connections"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Database Connections",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "FreeableMemory", {"stat": "Average", "label": "Free Memory"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Freeable Memory",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "FreeStorageSpace", {"stat": "Average", "label": "Free Storage"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Free Storage Space",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "ReadLatency", {"stat": "Average", "label": "Read Latency"}],
          [".", "WriteLatency", {"stat": "Average", "label": "Write Latency"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Read/Write Latency",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "ReadThroughput", {"stat": "Average", "label": "Read Throughput"}],
          [".", "WriteThroughput", {"stat": "Average", "label": "Write Throughput"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${AWS_REGION}",
        "title": "Read/Write Throughput",
        "yAxis": {"left": {"min": 0}}
      }
    }
  ]
}
EOF
)

aws cloudwatch put-dashboard \
    --dashboard-name "$CLOUDWATCH_DASHBOARD_NAME" \
    --dashboard-body "$DASHBOARD_BODY"
echo -e "${GREEN}✓ CloudWatch dashboard created${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^SNS_TOPIC_ARN=.*|SNS_TOPIC_ARN=\"${SNS_TOPIC_ARN}\"|" \
    -e "s|^SNS_SUBSCRIPTION_ARN=.*|SNS_SUBSCRIPTION_ARN=\"${SNS_SUBSCRIPTION_ARN}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CloudWatch Monitoring Created!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  SNS Topic:          ${SNS_TOPIC_ARN}"
echo -e "  Alert Email:        ${ALERT_EMAIL}"
echo -e "  Dashboard:          ${CLOUDWATCH_DASHBOARD_NAME}"
echo ""
echo -e "${GREEN}Alarms created:${NC}"
echo -e "  1. ${PROJECT_NAME}-rds-cpu-high (>70% for 10 min)"
echo -e "  2. ${PROJECT_NAME}-rds-connections-high (>80 connections for 10 min)"
echo -e "  3. ${PROJECT_NAME}-rds-storage-low (<2 GB)"
echo -e "  4. ${PROJECT_NAME}-rds-memory-low (<500 MB for 10 min)"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Check your email (${ALERT_EMAIL}) and confirm the SNS subscription!${NC}"
echo ""
echo -e "${GREEN}View dashboard:${NC}"
echo -e "  https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${CLOUDWATCH_DASHBOARD_NAME}"
echo ""
