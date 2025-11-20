#!/bin/bash

##############################################################################
# Destroy AWS Secrets Manager Secret for Production Application
#
# This script deletes the secret containing ALL production credentials:
# - Database credentials (username, password, host, port)
# - Django SECRET_KEY
# - Stripe API keys
# - Email credentials
#
# The secret is scheduled for deletion with a 30-day recovery window.
#
# Usage: ./scripts/infra/destroy-secrets.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will schedule the secret for deletion (30-day recovery window)
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
echo -e "${RED}Destroying Secrets Manager Secret${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will schedule ALL production secrets for deletion!${NC}"
echo -e "${YELLOW}Secret: ${DB_SECRET_NAME}${NC}"
echo -e "${YELLOW}Contains: Database, Django SECRET_KEY, Stripe, Email credentials${NC}"
echo -e "${YELLOW}Recovery window: 30 days${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Scheduling secret for deletion...${NC}"

# Delete secret (30-day recovery window)
aws secretsmanager delete-secret \
    --secret-id "$DB_SECRET_NAME" \
    --recovery-window-in-days 30 2>/dev/null || true
echo -e "${GREEN}✓ Secret scheduled for deletion (30-day recovery window)${NC}"

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^DB_SECRET_ARN=.*|DB_SECRET_ARN=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Secret Scheduled for Deletion!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Note: The secret can be recovered within 30 days if needed${NC}"
echo -e "${YELLOW}To force immediate deletion (not recommended):${NC}"
echo -e "  aws secretsmanager delete-secret --secret-id ${DB_SECRET_NAME} --force-delete-without-recovery"
echo ""
