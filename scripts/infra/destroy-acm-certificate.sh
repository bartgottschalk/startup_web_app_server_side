#!/bin/bash

##############################################################################
# Destroy ACM Certificate for StartupWebApp
#
# This script deletes:
# - ACM certificate
#
# WARNING:
# - Certificate cannot be deleted if it's attached to an ALB listener
# - You must destroy HTTPS listener first: ./scripts/infra/destroy-alb-https-listener.sh
#
# Usage: ./scripts/infra/destroy-acm-certificate.sh
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

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROY ACM Certificate${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if certificate exists
if [ -z "${ACM_CERTIFICATE_ARN:-}" ]; then
    echo -e "${YELLOW}No ACM Certificate ARN found in aws-resources.env${NC}"
    echo -e "${GREEN}Nothing to delete.${NC}"
    exit 0
fi

# Get certificate details
CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Certificate.Status' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$CERT_STATUS" == "NOT_FOUND" ]; then
    echo -e "${YELLOW}Certificate not found in AWS, clearing env file...${NC}"
    sed -i.bak \
        -e "s|^ACM_CERTIFICATE_ARN=.*|ACM_CERTIFICATE_ARN=\"\"|" \
        "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}✓ aws-resources.env cleared${NC}"
    exit 0
fi

# Check if certificate is in use
IN_USE=$(aws acm describe-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Certificate.InUseBy' \
    --output text 2>/dev/null || echo "")

if [ -n "$IN_USE" ] && [ "$IN_USE" != "None" ]; then
    echo -e "${RED}ERROR: Certificate is in use by:${NC}"
    echo -e "  ${IN_USE}"
    echo ""
    echo -e "${YELLOW}You must remove the HTTPS listener from ALB first:${NC}"
    echo -e "  1. Delete HTTPS listener from ALB"
    echo -e "  2. Then run this script again"
    exit 1
fi

# Confirm destruction
echo -e "${RED}WARNING: This will delete the ACM certificate!${NC}"
echo ""
echo -e "${YELLOW}Certificate ARN: ${ACM_CERTIFICATE_ARN}${NC}"
echo -e "${YELLOW}Status: ${CERT_STATUS}${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Step 1: Delete certificate
echo ""
echo -e "${YELLOW}Step 1: Deleting ACM certificate...${NC}"

aws acm delete-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}"

echo -e "${GREEN}✓ Certificate deleted${NC}"

# Step 2: Clear environment file
echo ""
echo -e "${YELLOW}Step 2: Clearing aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ACM_CERTIFICATE_ARN=.*|ACM_CERTIFICATE_ARN=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ACM Certificate Deleted!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Notes:${NC}"
echo -e "  - You can remove the DNS validation CNAME from Namecheap (optional)"
echo -e "  - To create a new certificate: ./scripts/infra/create-acm-certificate.sh"
echo ""
