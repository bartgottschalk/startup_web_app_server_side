#!/bin/bash

##############################################################################
# Create IAM Roles for ECS Tasks
#
# This script creates:
# - ECS Task Execution Role (for pulling images, reading secrets)
# - ECS Task Role (for application permissions)
#
# Usage: ./scripts/infra/create-ecs-task-role.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: Secrets Manager secret must exist
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
TASK_EXECUTION_ROLE_NAME="ecsTaskExecutionRole-${PROJECT_NAME}"
TASK_ROLE_NAME="ecsTaskRole-${PROJECT_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create IAM Roles for ECS Tasks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify secrets exist
if [ -z "${DB_SECRET_ARN:-}" ]; then
    echo -e "${RED}Error: DB_SECRET_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-secrets.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Using secret: ${DB_SECRET_NAME}${NC}"
echo ""

# Check if roles already exist
if [ -n "${ECS_TASK_EXECUTION_ROLE_ARN:-}" ]; then
    echo -e "${YELLOW}ECS IAM roles already exist${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-ecs-task-role.sh first${NC}"
    exit 0
fi

#############################################
# Create ECS Task Execution Role
#############################################

echo -e "${YELLOW}Creating ECS Task Execution Role...${NC}"

# Create trust policy for ECS tasks
cat > /tmp/ecs-task-execution-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
TASK_EXECUTION_ROLE_ARN=$(aws iam create-role \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" \
    --assume-role-policy-document file:///tmp/ecs-task-execution-trust-policy.json \
    --description "ECS Task Execution Role for ${PROJECT_NAME} - pulls images and reads secrets" \
    --tags Key=Name,Value="${TASK_EXECUTION_ROLE_NAME}" \
           Key=Environment,Value="${ENVIRONMENT}" \
           Key=Application,Value=StartupWebApp \
           Key=ManagedBy,Value=InfrastructureAsCode \
    --query 'Role.Arn' \
    --output text)

rm /tmp/ecs-task-execution-trust-policy.json

echo -e "${GREEN}✓ ECS Task Execution Role created${NC}"
echo -e "  ARN: ${TASK_EXECUTION_ROLE_ARN}"

# Attach AWS managed policy for ECS task execution (ECR + CloudWatch Logs)
echo -e "${YELLOW}Attaching managed policy: AmazonECSTaskExecutionRolePolicy...${NC}"
aws iam attach-role-policy \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

echo -e "${GREEN}✓ Attached AmazonECSTaskExecutionRolePolicy${NC}"

# Create inline policy for Secrets Manager access
echo -e "${YELLOW}Creating Secrets Manager access policy...${NC}"

cat > /tmp/ecs-secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "${DB_SECRET_ARN}"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name "${TASK_EXECUTION_ROLE_NAME}" \
    --policy-name "SecretsManagerAccess" \
    --policy-document file:///tmp/ecs-secrets-policy.json

rm /tmp/ecs-secrets-policy.json

echo -e "${GREEN}✓ Secrets Manager access policy created${NC}"

#############################################
# Create ECS Task Role (for application)
#############################################

echo -e "${YELLOW}Creating ECS Task Role...${NC}"

# Create the role (same trust policy)
cat > /tmp/ecs-task-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

TASK_ROLE_ARN=$(aws iam create-role \
    --role-name "${TASK_ROLE_NAME}" \
    --assume-role-policy-document file:///tmp/ecs-task-trust-policy.json \
    --description "ECS Task Role for ${PROJECT_NAME} - application runtime permissions" \
    --tags Key=Name,Value="${TASK_ROLE_NAME}" \
           Key=Environment,Value="${ENVIRONMENT}" \
           Key=Application,Value=StartupWebApp \
           Key=ManagedBy,Value=InfrastructureAsCode \
    --query 'Role.Arn' \
    --output text)

rm /tmp/ecs-task-trust-policy.json

echo -e "${GREEN}✓ ECS Task Role created${NC}"
echo -e "  ARN: ${TASK_ROLE_ARN}"

# Create inline policy for application runtime (Secrets Manager read access)
echo -e "${YELLOW}Creating application runtime policy...${NC}"

cat > /tmp/ecs-task-runtime-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "${DB_SECRET_ARN}"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name "${TASK_ROLE_NAME}" \
    --policy-name "ApplicationRuntimeAccess" \
    --policy-document file:///tmp/ecs-task-runtime-policy.json

rm /tmp/ecs-task-runtime-policy.json

echo -e "${GREEN}✓ Application runtime policy created${NC}"

# Wait for IAM roles to propagate
echo -e "${YELLOW}Waiting 10 seconds for IAM roles to propagate...${NC}"
sleep 10
echo -e "${GREEN}✓ IAM roles propagated${NC}"

# Save to env file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECS_TASK_EXECUTION_ROLE_ARN=.*|ECS_TASK_EXECUTION_ROLE_ARN=\"${TASK_EXECUTION_ROLE_ARN}\"|" \
    -e "s|^ECS_TASK_EXECUTION_ROLE_NAME=.*|ECS_TASK_EXECUTION_ROLE_NAME=\"${TASK_EXECUTION_ROLE_NAME}\"|" \
    -e "s|^ECS_TASK_ROLE_ARN=.*|ECS_TASK_ROLE_ARN=\"${TASK_ROLE_ARN}\"|" \
    -e "s|^ECS_TASK_ROLE_NAME=.*|ECS_TASK_ROLE_NAME=\"${TASK_ROLE_NAME}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}IAM Roles Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo ""
echo -e "${GREEN}Task Execution Role:${NC}"
echo -e "  Name:        ${TASK_EXECUTION_ROLE_NAME}"
echo -e "  ARN:         ${TASK_EXECUTION_ROLE_ARN}"
echo -e "  Purpose:     Pull ECR images, write CloudWatch logs, read secrets"
echo -e "  Policies:"
echo -e "    - AmazonECSTaskExecutionRolePolicy (AWS managed)"
echo -e "    - SecretsManagerAccess (inline)"
echo ""
echo -e "${GREEN}Task Role:${NC}"
echo -e "  Name:        ${TASK_ROLE_NAME}"
echo -e "  ARN:         ${TASK_ROLE_ARN}"
echo -e "  Purpose:     Application runtime permissions"
echo -e "  Policies:"
echo -e "    - ApplicationRuntimeAccess (inline - Secrets Manager)"
echo ""
echo -e "${GREEN}Cost Estimate:${NC}"
echo -e "  IAM Roles:   \$0 (no cost for IAM roles)"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Update security groups for ECS:"
echo -e "     ./scripts/infra/update-security-groups-ecs.sh"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  ✓ Step 3: Create ECS Cluster"
echo -e "  ✓ Step 4: Create IAM Roles for ECS"
echo -e "  → Step 5: Update Security Groups"
echo ""
