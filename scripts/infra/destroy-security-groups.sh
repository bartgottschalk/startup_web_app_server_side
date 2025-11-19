#!/bin/bash

##############################################################################
# Destroy Security Groups for StartupWebApp
#
# This script deletes all security groups created for the project
#
# Usage: ./scripts/infra/destroy-security-groups.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will DELETE all security groups
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

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroying Security Groups${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will DELETE all security groups!${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - RDS SG: ${RDS_SECURITY_GROUP_ID}"
echo -e "  - Bastion SG: ${BASTION_SECURITY_GROUP_ID}"
echo -e "  - Backend SG: ${BACKEND_SECURITY_GROUP_ID}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting destruction...${NC}"
echo ""

# Delete security groups (order matters for dependencies)
for sg_id in "$BACKEND_SECURITY_GROUP_ID" "$BASTION_SECURITY_GROUP_ID" "$RDS_SECURITY_GROUP_ID"; do
    if [ -n "$sg_id" ]; then
        echo -e "${YELLOW}Deleting Security Group: ${sg_id}...${NC}"
        aws ec2 delete-security-group --group-id "$sg_id" 2>/dev/null || true
        echo -e "${GREEN}✓ Security Group deleted${NC}"
    fi
done

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^RDS_SECURITY_GROUP_ID=.*|RDS_SECURITY_GROUP_ID=\"\"|" \
    -e "s|^BASTION_SECURITY_GROUP_ID=.*|BASTION_SECURITY_GROUP_ID=\"\"|" \
    -e "s|^BACKEND_SECURITY_GROUP_ID=.*|BACKEND_SECURITY_GROUP_ID=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Security Groups Destroyed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
