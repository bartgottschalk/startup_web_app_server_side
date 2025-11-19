#!/bin/bash

##############################################################################
# Destroy CloudWatch Monitoring for StartupWebApp
#
# This script deletes:
# - CloudWatch alarms
# - CloudWatch dashboard
# - SNS subscriptions
# - SNS topic
#
# Usage: ./scripts/infra/destroy-monitoring.sh
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
echo -e "${RED}Destroying CloudWatch Monitoring${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will DELETE all monitoring configuration!${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - SNS Topic: ${SNS_TOPIC_ARN}"
echo -e "  - All CloudWatch alarms"
echo -e "  - Dashboard: ${CLOUDWATCH_DASHBOARD_NAME}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting destruction...${NC}"
echo ""

# Delete CloudWatch Alarms
echo -e "${YELLOW}Deleting CloudWatch alarms...${NC}"
ALARMS=("${PROJECT_NAME}-rds-cpu-high" "${PROJECT_NAME}-rds-connections-high" "${PROJECT_NAME}-rds-storage-low" "${PROJECT_NAME}-rds-memory-low")
for alarm in "${ALARMS[@]}"; do
    aws cloudwatch delete-alarms --alarm-names "$alarm" 2>/dev/null || true
    echo -e "${GREEN}✓ Alarm deleted: ${alarm}${NC}"
done

# Delete CloudWatch Dashboard
echo -e "${YELLOW}Deleting CloudWatch dashboard...${NC}"
aws cloudwatch delete-dashboards --dashboard-names "$CLOUDWATCH_DASHBOARD_NAME" 2>/dev/null || true
echo -e "${GREEN}✓ Dashboard deleted${NC}"

# Unsubscribe from SNS topic
if [ -n "${SNS_SUBSCRIPTION_ARN:-}" ] && [ "$SNS_SUBSCRIPTION_ARN" != "pending confirmation" ]; then
    echo -e "${YELLOW}Unsubscribing from SNS topic...${NC}"
    aws sns unsubscribe --subscription-arn "$SNS_SUBSCRIPTION_ARN" 2>/dev/null || true
    echo -e "${GREEN}✓ Unsubscribed${NC}"
fi

# Delete SNS topic
if [ -n "$SNS_TOPIC_ARN" ]; then
    echo -e "${YELLOW}Deleting SNS topic...${NC}"
    aws sns delete-topic --topic-arn "$SNS_TOPIC_ARN" 2>/dev/null || true
    echo -e "${GREEN}✓ SNS topic deleted${NC}"
fi

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^SNS_TOPIC_ARN=.*|SNS_TOPIC_ARN=\"\"|" \
    -e "s|^SNS_SUBSCRIPTION_ARN=.*|SNS_SUBSCRIPTION_ARN=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CloudWatch Monitoring Destroyed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
