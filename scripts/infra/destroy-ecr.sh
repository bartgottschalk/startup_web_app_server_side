#!/bin/bash

##############################################################################
# Destroy AWS ECR Repository for StartupWebApp Backend
#
# This script deletes:
# - ECR repository
# - All Docker images in the repository
#
# Usage: ./scripts/infra/destroy-ecr.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will delete all Docker images in the repository!
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
REPOSITORY_NAME="${PROJECT_NAME}-backend"

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY AWS ECR Repository${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will delete all Docker images in the repository!${NC}"
echo -e "${YELLOW}Repository: ${REPOSITORY_NAME}${NC}"
if [ -n "${ECR_REPOSITORY_URI:-}" ]; then
    echo -e "${YELLOW}URI: ${ECR_REPOSITORY_URI}${NC}"
fi
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Deleting ECR repository (force delete with all images)...${NC}"

# Delete repository (force delete removes all images)
aws ecr delete-repository \
    --repository-name "${REPOSITORY_NAME}" \
    --region "${AWS_REGION}" \
    --force > /dev/null 2>&1 || true

echo -e "${GREEN}✓ ECR repository deleted${NC}"

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^ECR_REPOSITORY_URI=.*|ECR_REPOSITORY_URI=\"\"|" \
    -e "s|^ECR_REPOSITORY_NAME=.*|ECR_REPOSITORY_NAME=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ECR Repository Deleted!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Note: All Docker images have been permanently deleted${NC}"
echo ""
