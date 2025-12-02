#!/bin/bash

##############################################################################
# Destroy HTTPS Listener for ALB - StartupWebApp
#
# This script deletes:
# - HTTPS listener (port 443) from the ALB
#
# WARNING:
# - After removal, HTTPS traffic will fail (connection refused)
# - HTTP traffic continues to redirect to HTTPS (which will fail)
# - You should recreate the listener or destroy the ALB
#
# Use cases:
# - Before destroying ACM certificate
# - Troubleshooting certificate issues
# - Switching to a different certificate
#
# Usage: ./scripts/infra/destroy-alb-https-listener.sh
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

echo -e "${RED}========================================"
echo -e "Destroy HTTPS Listener for ALB"
echo -e "========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if HTTPS listener exists in env
if [ -z "${HTTPS_LISTENER_ARN:-}" ]; then
    echo -e "${YELLOW}No HTTPS_LISTENER_ARN found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to destroy.${NC}"
    exit 0
fi

# Verify listener exists in AWS
LISTENER_EXISTS=$(aws elbv2 describe-listeners \
    --listener-arns "${HTTPS_LISTENER_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Listeners[0].ListenerArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$LISTENER_EXISTS" ] || [ "$LISTENER_EXISTS" == "None" ]; then
    echo -e "${YELLOW}HTTPS Listener not found in AWS, clearing env file...${NC}"
    sed -i.bak \
        -e "s|^HTTPS_LISTENER_ARN=.*|HTTPS_LISTENER_ARN=\"\"|" \
        "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
    exit 0
fi

# Confirm destruction
echo -e "${RED}WARNING: This will destroy the HTTPS listener from the ALB!${NC}"
echo -e "${RED}HTTPS traffic will fail after this operation.${NC}"
echo ""
echo -e "${YELLOW}Listener to be destroyed:${NC}"
echo -e "  HTTPS Listener ARN: ${HTTPS_LISTENER_ARN}"
echo ""
echo -e "${YELLOW}Impact:${NC}"
echo -e "  - HTTPS (port 443) traffic will fail"
echo -e "  - HTTP (port 80) will still redirect to HTTPS (which fails)"
echo -e "  - ACM certificate can be deleted after this"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Delete HTTPS Listener
echo ""
echo -e "${YELLOW}Step 1: Deleting HTTPS Listener...${NC}"

aws elbv2 delete-listener \
    --listener-arn "${HTTPS_LISTENER_ARN}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ HTTPS Listener deleted${NC}"

# Step 2: Clear environment file
echo ""
echo -e "${YELLOW}Step 2: Clearing HTTPS_LISTENER_ARN from aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^HTTPS_LISTENER_ARN=.*|HTTPS_LISTENER_ARN=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================"
echo -e "HTTPS Listener Destroyed!"
echo -e "========================================${NC}"
echo ""
echo -e "${YELLOW}Current State:${NC}"
echo -e "  - ALB still exists (HTTP listener active)"
echo -e "  - HTTP (80) redirects to HTTPS (443)"
echo -e "  - HTTPS (443) will fail (no listener)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  Option A: Recreate HTTPS listener"
echo -e "    ./scripts/infra/create-alb-https-listener.sh"
echo ""
echo -e "  Option B: Delete ACM certificate"
echo -e "    ./scripts/infra/destroy-acm-certificate.sh"
echo ""
echo -e "  Option C: Destroy entire ALB"
echo -e "    ./scripts/infra/destroy-alb.sh"
echo ""
