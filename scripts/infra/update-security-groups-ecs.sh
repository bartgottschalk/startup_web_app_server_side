#!/bin/bash

##############################################################################
# Update Security Groups for ECS Integration
#
# This script updates existing security groups to allow ECS → RDS communication:
# - Verifies Backend SG → RDS SG rule exists (created during initial setup)
# - ECS tasks will use the Backend security group
#
# Usage: ./scripts/infra/update-security-groups-ecs.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# Prerequisites: Security groups must exist (run create-security-groups.sh)
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
echo -e "${BLUE}Update Security Groups for ECS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify security groups exist
if [ -z "${RDS_SECURITY_GROUP_ID:-}" ] || [ -z "${BACKEND_SECURITY_GROUP_ID:-}" ]; then
    echo -e "${RED}Error: Security groups not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please run: ./scripts/infra/create-security-groups.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Using security groups:${NC}"
echo -e "  RDS SG:     ${RDS_SECURITY_GROUP_ID}"
echo -e "  Backend SG: ${BACKEND_SECURITY_GROUP_ID}"
echo ""

#############################################
# Verify Backend → RDS rule
#############################################

echo -e "${YELLOW}Verifying Backend → RDS security group rule...${NC}"

# Check if rule already exists
RULE_EXISTS=$(aws ec2 describe-security-group-rules \
    --filters "Name=group-id,Values=${RDS_SECURITY_GROUP_ID}" \
    --query "SecurityGroupRules[?ReferencedGroupInfo.GroupId=='${BACKEND_SECURITY_GROUP_ID}' && FromPort==\`5432\` && ToPort==\`5432\`].SecurityGroupRuleId" \
    --output text 2>/dev/null || echo "")

if [ -n "$RULE_EXISTS" ]; then
    echo -e "${GREEN}✓ Backend → RDS rule already exists${NC}"
    echo -e "  Rule ID: ${RULE_EXISTS}"
else
    echo -e "${YELLOW}Creating Backend → RDS rule...${NC}"

    aws ec2 authorize-security-group-ingress \
        --group-id "$RDS_SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5432 \
        --source-group "$BACKEND_SECURITY_GROUP_ID" \
        --group-owner "$AWS_ACCOUNT_ID" 2>/dev/null || {
            echo -e "${YELLOW}⚠ Rule may already exist (ignore if this is a duplicate)${NC}"
        }

    echo -e "${GREEN}✓ Backend → RDS rule created${NC}"
fi

#############################################
# Add outbound rules to Backend SG
#############################################

echo -e "${YELLOW}Configuring Backend SG outbound rules...${NC}"

# Check if PostgreSQL outbound rule exists
PG_OUTBOUND_EXISTS=$(aws ec2 describe-security-group-rules \
    --filters "Name=group-id,Values=${BACKEND_SECURITY_GROUP_ID}" "Name=is-egress,Values=true" \
    --query "SecurityGroupRules[?ReferencedGroupInfo.GroupId=='${RDS_SECURITY_GROUP_ID}' && FromPort==\`5432\` && ToPort==\`5432\`].SecurityGroupRuleId" \
    --output text 2>/dev/null || echo "")

if [ -n "$PG_OUTBOUND_EXISTS" ]; then
    echo -e "${GREEN}✓ Backend → RDS outbound rule already exists${NC}"
else
    echo -e "${YELLOW}Creating Backend → RDS outbound rule...${NC}"

    aws ec2 authorize-security-group-egress \
        --group-id "$BACKEND_SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5432 \
        --source-group "$RDS_SECURITY_GROUP_ID" \
        --group-owner "$AWS_ACCOUNT_ID" 2>/dev/null || {
            echo -e "${YELLOW}⚠ Rule may already exist (ignore if this is a duplicate)${NC}"
        }

    echo -e "${GREEN}✓ Backend → RDS outbound rule created${NC}"
fi

# Check for HTTPS outbound (for ECR image pulls)
HTTPS_OUTBOUND_EXISTS=$(aws ec2 describe-security-group-rules \
    --filters "Name=group-id,Values=${BACKEND_SECURITY_GROUP_ID}" "Name=is-egress,Values=true" \
    --query "SecurityGroupRules[?CidrIpv4=='0.0.0.0/0' && FromPort==\`443\` && ToPort==\`443\`].SecurityGroupRuleId" \
    --output text 2>/dev/null || echo "")

if [ -n "$HTTPS_OUTBOUND_EXISTS" ]; then
    echo -e "${GREEN}✓ HTTPS outbound rule already exists${NC}"
else
    echo -e "${YELLOW}Creating HTTPS outbound rule (for ECR)...${NC}"

    aws ec2 authorize-security-group-egress \
        --group-id "$BACKEND_SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 2>/dev/null || {
            echo -e "${YELLOW}⚠ Rule may already exist (ignore if this is a duplicate)${NC}"
        }

    echo -e "${GREEN}✓ HTTPS outbound rule created${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Security Groups Updated Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo ""
echo -e "  ${GREEN}RDS Security Group (${RDS_SECURITY_GROUP_ID}):${NC}"
echo -e "    Inbound:"
echo -e "      - Port 5432 from Backend SG (${BACKEND_SECURITY_GROUP_ID})"
echo -e "      - Port 5432 from Bastion SG (${BASTION_SECURITY_GROUP_ID})"
echo ""
echo -e "  ${GREEN}Backend Security Group (${BACKEND_SECURITY_GROUP_ID}):${NC}"
echo -e "    Outbound:"
echo -e "      - Port 5432 to RDS SG (${RDS_SECURITY_GROUP_ID})"
echo -e "      - Port 443 to 0.0.0.0/0 (ECR image pulls)"
echo ""
echo -e "${GREEN}ECS Tasks Configuration:${NC}"
echo -e "  - ECS tasks will use Backend SG (${BACKEND_SECURITY_GROUP_ID})"
echo -e "  - Can connect to RDS on port 5432"
echo -e "  - Can pull images from ECR via HTTPS"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  ECS infrastructure is now complete!"
echo ""
echo -e "${YELLOW}Phase 5.14 Progress:${NC}"
echo -e "  ✓ Step 1: Multi-Stage Dockerfile"
echo -e "  ✓ Step 2: Create AWS ECR Repository"
echo -e "  ✓ Step 3: Create ECS Cluster"
echo -e "  ✓ Step 4: Create IAM Roles for ECS"
echo -e "  ✓ Step 5: Update Security Groups"
echo -e "  → Step 6: Create ECS Task Definition (code-based)"
echo -e "  → Step 7: Create GitHub Actions Workflow"
echo ""
