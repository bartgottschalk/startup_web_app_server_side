#!/bin/bash

##############################################################################
# Destroy Bastion Host
#
# This script destroys:
# - EC2 bastion instance
# - IAM instance profile
# - IAM role
#
# Usage: ./scripts/infra/destroy-bastion.sh
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

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Destroying Bastion Host${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Find all bastion instances by tag (not just from env file)
echo -e "${YELLOW}Step 1: Finding bastion instances...${NC}"
BASTION_INSTANCES=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-bastion" \
              "Name=instance-state-name,Values=running,stopped,pending,stopping" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text)

if [ -n "$BASTION_INSTANCES" ]; then
    echo -e "${GREEN}Found bastion instance(s): ${BASTION_INSTANCES}${NC}"
    echo -e "${YELLOW}Terminating bastion instance(s)...${NC}"

    for INSTANCE_ID in $BASTION_INSTANCES; do
        aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"
        echo -e "${GREEN}✓ Termination initiated for ${INSTANCE_ID}${NC}"
    done

    echo -e "${YELLOW}Waiting for instance(s) to terminate (this takes ~30 seconds)...${NC}"
    for INSTANCE_ID in $BASTION_INSTANCES; do
        aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ All instances terminated${NC}"
else
    echo -e "${YELLOW}No running bastion instances found${NC}"

    # Also check from env file as fallback
    if [ -n "${BASTION_INSTANCE_ID:-}" ]; then
        echo -e "${YELLOW}Checking instance from env file: ${BASTION_INSTANCE_ID}${NC}"
        INSTANCE_STATE=$(aws ec2 describe-instances \
            --instance-ids "$BASTION_INSTANCE_ID" \
            --query 'Reservations[0].Instances[0].State.Name' \
            --output text 2>/dev/null || echo "not-found")

        if [ "$INSTANCE_STATE" != "not-found" ] && [ "$INSTANCE_STATE" != "terminated" ]; then
            aws ec2 terminate-instances --instance-ids "$BASTION_INSTANCE_ID"
            echo -e "${GREEN}✓ Termination initiated for ${BASTION_INSTANCE_ID}${NC}"
            aws ec2 wait instance-terminated --instance-ids "$BASTION_INSTANCE_ID" 2>/dev/null || true
            echo -e "${GREEN}✓ Instance terminated${NC}"
        fi
    fi
fi

# Remove role from instance profile
echo -e "${YELLOW}Step 2: Removing role from instance profile...${NC}"
aws iam remove-role-from-instance-profile \
    --instance-profile-name "${PROJECT_NAME}-bastion-profile" \
    --role-name "${PROJECT_NAME}-bastion-role" 2>/dev/null || echo -e "${YELLOW}Role not in instance profile (may already be removed)${NC}"

# Delete instance profile
echo -e "${YELLOW}Step 3: Deleting instance profile...${NC}"
aws iam delete-instance-profile \
    --instance-profile-name "${PROJECT_NAME}-bastion-profile" 2>/dev/null || echo -e "${YELLOW}Instance profile not found (may already be deleted)${NC}"
echo -e "${GREEN}✓ Instance profile deleted${NC}"

# Detach policies from role
echo -e "${YELLOW}Step 4: Detaching policies from IAM role...${NC}"
aws iam detach-role-policy \
    --role-name "${PROJECT_NAME}-bastion-role" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore" 2>/dev/null || echo -e "${YELLOW}Policy not attached (may already be detached)${NC}"
echo -e "${GREEN}✓ Policies detached${NC}"

# Delete IAM role
echo -e "${YELLOW}Step 5: Deleting IAM role...${NC}"
aws iam delete-role \
    --role-name "${PROJECT_NAME}-bastion-role" 2>/dev/null || echo -e "${YELLOW}Role not found (may already be deleted)${NC}"
echo -e "${GREEN}✓ IAM role deleted${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^BASTION_INSTANCE_ID=.*|BASTION_INSTANCE_ID=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bastion Host Destroyed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Resources removed:${NC}"
echo -e "  - EC2 instance"
echo -e "  - IAM instance profile"
echo -e "  - IAM role"
echo ""
echo -e "${YELLOW}Note: Bastion security group NOT deleted (shared resource)${NC}"
echo -e "  You can delete it manually if no longer needed:"
echo -e "  aws ec2 delete-security-group --group-id ${BASTION_SECURITY_GROUP_ID}"
echo ""
