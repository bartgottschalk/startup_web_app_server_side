#!/bin/bash

##############################################################################
# Destroy ECS Auto-Scaling for StartupWebApp
#
# This script removes:
# - CPU scaling policy
# - Memory scaling policy
# - Application Auto Scaling target
#
# After running this script, the ECS service will maintain a fixed task count
# (the current desired count at time of removal).
#
# Usage: ./scripts/infra/destroy-ecs-autoscaling.sh
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Destroy ECS Auto-Scaling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
echo -e "${YELLOW}Checking for existing auto-scaling configuration...${NC}"

if [ -z "${ECS_CLUSTER_NAME:-}" ] || [ -z "${ECS_SERVICE_NAME:-}" ]; then
    echo -e "${RED}Error: ECS_CLUSTER_NAME or ECS_SERVICE_NAME not found${NC}"
    exit 1
fi

# Construct resource ID
RESOURCE_ID="service/${ECS_CLUSTER_NAME}/${ECS_SERVICE_NAME}"

# Check if scalable target exists
EXISTING_TARGET=$(aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "${RESOURCE_ID}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].ResourceId' \
    --output text 2>/dev/null || echo "None")

if [ "$EXISTING_TARGET" == "None" ] || [ -z "$EXISTING_TARGET" ]; then
    echo -e "${YELLOW}No auto-scaling configuration found for ${ECS_SERVICE_NAME}${NC}"
    echo -e "${YELLOW}Nothing to destroy.${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Found auto-scaling configuration${NC}"
echo ""

# Get current configuration
CURRENT_CONFIG=$(aws application-autoscaling describe-scalable-targets \
    --service-namespace ecs \
    --resource-ids "${RESOURCE_ID}" \
    --region "${AWS_REGION}" \
    --query 'ScalableTargets[0].{Min: MinCapacity, Max: MaxCapacity}' \
    --output json)

CURRENT_MIN=$(echo "$CURRENT_CONFIG" | jq -r '.Min')
CURRENT_MAX=$(echo "$CURRENT_CONFIG" | jq -r '.Max')

# Get scaling policies
POLICIES=$(aws application-autoscaling describe-scaling-policies \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --region "${AWS_REGION}" \
    --query 'ScalingPolicies[*].PolicyName' \
    --output json)

echo -e "${YELLOW}Current Configuration:${NC}"
echo -e "  Resource ID:            ${RESOURCE_ID}"
echo -e "  Min Capacity:           ${CURRENT_MIN}"
echo -e "  Max Capacity:           ${CURRENT_MAX}"
echo -e "  Scaling Policies:       $(echo "$POLICIES" | jq -r 'join(", ")')"
echo ""

echo -e "${RED}WARNING: This will remove auto-scaling for the ECS service.${NC}"
echo -e "${RED}The service will maintain its current task count after removal.${NC}"
echo ""

read -p "Are you sure you want to destroy auto-scaling? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Delete scaling policies
echo ""
echo -e "${YELLOW}Step 1: Deleting scaling policies...${NC}"

# Delete CPU policy
CPU_POLICY_NAME="${PROJECT_NAME}-cpu-scaling"
if aws application-autoscaling delete-scaling-policy \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --policy-name "${CPU_POLICY_NAME}" \
    --region "${AWS_REGION}" 2>/dev/null; then
    echo -e "${GREEN}✓ Deleted CPU scaling policy: ${CPU_POLICY_NAME}${NC}"
else
    echo -e "${YELLOW}  CPU policy not found or already deleted${NC}"
fi

# Delete Memory policy
MEMORY_POLICY_NAME="${PROJECT_NAME}-memory-scaling"
if aws application-autoscaling delete-scaling-policy \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --policy-name "${MEMORY_POLICY_NAME}" \
    --region "${AWS_REGION}" 2>/dev/null; then
    echo -e "${GREEN}✓ Deleted Memory scaling policy: ${MEMORY_POLICY_NAME}${NC}"
else
    echo -e "${YELLOW}  Memory policy not found or already deleted${NC}"
fi

# Step 2: Deregister scalable target
echo ""
echo -e "${YELLOW}Step 2: Deregistering scalable target...${NC}"

aws application-autoscaling deregister-scalable-target \
    --service-namespace ecs \
    --resource-id "${RESOURCE_ID}" \
    --scalable-dimension "ecs:service:DesiredCount" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ Scalable target deregistered${NC}"

# Step 3: Update aws-resources.env
echo ""
echo -e "${YELLOW}Step 3: Updating aws-resources.env...${NC}"

# Remove auto-scaling variables from env file
if grep -q "^AUTOSCALING_MIN_CAPACITY=" "$ENV_FILE"; then
    sed -i.bak \
        -e '/^# ECS Auto-Scaling/d' \
        -e '/^AUTOSCALING_MIN_CAPACITY=/d' \
        -e '/^AUTOSCALING_MAX_CAPACITY=/d' \
        -e '/^AUTOSCALING_CPU_POLICY=/d' \
        -e '/^AUTOSCALING_MEMORY_POLICY=/d' \
        "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env updated${NC}"
else
    echo -e "${YELLOW}  No auto-scaling variables found in env file${NC}"
fi

# Step 4: Get current service status
echo ""
echo -e "${YELLOW}Step 4: Verifying service status...${NC}"

SERVICE_STATUS=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER_NAME}" \
    --services "${ECS_SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'services[0].{running: runningCount, desired: desiredCount}' \
    --output json)

RUNNING=$(echo "$SERVICE_STATUS" | jq -r '.running')
DESIRED=$(echo "$SERVICE_STATUS" | jq -r '.desired')

echo -e "  Service: ${ECS_SERVICE_NAME}"
echo -e "  Running tasks: ${RUNNING}"
echo -e "  Desired tasks: ${DESIRED}"
echo -e "${GREEN}✓ Service will maintain ${DESIRED} task(s)${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Auto-Scaling Destroyed Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Removed:${NC}"
echo -e "  • CPU scaling policy: ${CPU_POLICY_NAME}"
echo -e "  • Memory scaling policy: ${MEMORY_POLICY_NAME}"
echo -e "  • Scalable target for: ${RESOURCE_ID}"
echo ""
echo -e "${GREEN}Current State:${NC}"
echo -e "  • Service ${ECS_SERVICE_NAME} is running ${RUNNING} task(s)"
echo -e "  • Task count will remain fixed at ${DESIRED}"
echo -e "  • No automatic scaling will occur"
echo ""
echo -e "${YELLOW}To re-enable auto-scaling:${NC}"
echo -e "  ./scripts/infra/create-ecs-autoscaling.sh"
echo ""
