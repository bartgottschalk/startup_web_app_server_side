#!/bin/bash

##############################################################################
# Create AWS ECS Cluster for StartupWebApp
#
# This script creates:
# - ECS Fargate cluster for running containerized tasks
# - CloudWatch log group for ECS tasks
#
# Usage: ./scripts/infra/create-ecs-cluster.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: VPC must be created first (run create-vpc.sh)
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
CLUSTER_NAME="${PROJECT_NAME}-cluster"
LOG_GROUP_NAME="/ecs/${PROJECT_NAME}-migrations"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create AWS ECS Cluster${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify VPC exists
if [ -z "${VPC_ID:-}" ]; then
    echo -e "${RED}Error: VPC_ID not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-vpc.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Using VPC: ${VPC_ID}${NC}"
echo ""

# Check if cluster already exists
if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
    echo -e "${YELLOW}Checking if ECS cluster exists...${NC}"
    EXISTING_CLUSTER=$(aws ecs describe-clusters \
        --clusters "${CLUSTER_NAME}" \
        --region "${AWS_REGION}" \
        --query 'clusters[0].clusterName' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_CLUSTER" ] && [ "$EXISTING_CLUSTER" != "None" ]; then
        echo -e "${GREEN}✓ ECS cluster already exists: ${EXISTING_CLUSTER}${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-ecs-cluster.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}Cluster name in env file but not found in AWS, creating new...${NC}"
    fi
fi

# Create ECS cluster
echo -e "${YELLOW}Creating ECS cluster...${NC}"
ECS_CLUSTER_ARN=$(aws ecs create-cluster \
    --cluster-name "${CLUSTER_NAME}" \
    --region "${AWS_REGION}" \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --tags key=Name,value="${CLUSTER_NAME}" \
           key=Environment,value="${ENVIRONMENT}" \
           key=Application,value=StartupWebApp \
           key=ManagedBy,value=InfrastructureAsCode \
    --query 'cluster.clusterArn' \
    --output text)

echo -e "${GREEN}✓ ECS cluster created: ${CLUSTER_NAME}${NC}"
echo -e "  ARN: ${ECS_CLUSTER_ARN}"

# Create CloudWatch log group for ECS tasks
echo -e "${YELLOW}Creating CloudWatch log group...${NC}"

# Check if log group already exists
EXISTING_LOG_GROUP=$(aws logs describe-log-groups \
    --log-group-name-prefix "${LOG_GROUP_NAME}" \
    --region "${AWS_REGION}" \
    --query "logGroups[?logGroupName=='${LOG_GROUP_NAME}'].logGroupName" \
    --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_LOG_GROUP" ]; then
    aws logs create-log-group \
        --log-group-name "${LOG_GROUP_NAME}" \
        --region "${AWS_REGION}"

    # Set retention policy (7 days)
    aws logs put-retention-policy \
        --log-group-name "${LOG_GROUP_NAME}" \
        --retention-in-days 7 \
        --region "${AWS_REGION}"

    echo -e "${GREEN}✓ CloudWatch log group created: ${LOG_GROUP_NAME}${NC}"
    echo -e "  Retention: 7 days"
else
    echo -e "${GREEN}✓ CloudWatch log group already exists: ${LOG_GROUP_NAME}${NC}"
fi

# Save to env file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_CLUSTER_NAME=.*|ECS_CLUSTER_NAME=\"${CLUSTER_NAME}\"|" \
    -e "s|^ECS_CLUSTER_ARN=.*|ECS_CLUSTER_ARN=\"${ECS_CLUSTER_ARN}\"|" \
    -e "s|^ECS_LOG_GROUP_NAME=.*|ECS_LOG_GROUP_NAME=\"${LOG_GROUP_NAME}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECS Cluster Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Cluster Name:        ${CLUSTER_NAME}"
echo -e "  Cluster ARN:         ${ECS_CLUSTER_ARN}"
echo -e "  Region:              ${AWS_REGION}"
echo -e "  Launch Type:         Fargate (serverless)"
echo -e "  Capacity Providers:  FARGATE, FARGATE_SPOT"
echo -e "  Log Group:           ${LOG_GROUP_NAME}"
echo -e "  Log Retention:       7 days"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  ECS Cluster:         \$0 (no cost for cluster itself)"
echo -e "  CloudWatch Logs:     ~\$0.50/GB ingested"
echo -e "  Fargate Tasks:       Pay-per-use (only when tasks run)"
echo -e "    - 0.25 vCPU:       ~\$0.01235/hour"
echo -e "    - 0.5 GB memory:   ~\$0.00135/hour"
echo -e "    - Total per task:  ~\$0.0137/hour"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Create IAM task roles:"
echo -e "     ./scripts/infra/create-ecs-task-role.sh"
echo ""
echo -e "  2. Update security groups for ECS:"
echo -e "     ./scripts/infra/update-security-groups-ecs.sh"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  ✓ Step 3: Create ECS Cluster"
echo -e "  → Step 4: Create IAM Roles for ECS"
echo ""
