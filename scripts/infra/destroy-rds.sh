#!/bin/bash

##############################################################################
# Destroy AWS RDS PostgreSQL Instance for StartupWebApp
#
# This script deletes the RDS instance
#
# Usage: ./scripts/infra/destroy-rds.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will DELETE the RDS instance and ALL databases
# Estimated time: 5-10 minutes (AWS deletion time)
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
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroying RDS PostgreSQL Instance${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Confirm destruction
echo -e "${RED}WARNING: This will DELETE the RDS instance and ALL databases!${NC}"
echo -e "${RED}Instance ID: ${RDS_INSTANCE_ID}${NC}"
echo -e "${RED}Endpoint: ${RDS_ENDPOINT}${NC}"
echo ""
echo -e "${YELLOW}ALL DATA WILL BE LOST!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'DELETE' to confirm): " confirm

if [ "$confirm" != "DELETE" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# Ask about final snapshot
echo ""
read -p "Create final snapshot before deletion? (yes/no): " create_snapshot

if [ "$create_snapshot" == "yes" ]; then
    SNAPSHOT_ID="${RDS_INSTANCE_ID}-final-snapshot-$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}Creating final snapshot: ${SNAPSHOT_ID}${NC}"

    # First, disable deletion protection
    echo -e "${YELLOW}Disabling deletion protection...${NC}"
    aws rds modify-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --no-deletion-protection \
        --apply-immediately > /dev/null
    echo -e "${GREEN}✓ Deletion protection disabled${NC}"

    # Wait a moment for the modification to take effect
    sleep 5

    # Delete with snapshot
    echo -e "${YELLOW}Deleting RDS instance with final snapshot...${NC}"
    aws rds delete-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --final-db-snapshot-identifier "$SNAPSHOT_ID" > /dev/null
    echo -e "${GREEN}✓ RDS instance deletion initiated with snapshot${NC}"
    echo -e "${GREEN}✓ Snapshot: ${SNAPSHOT_ID}${NC}"
else
    echo -e "${YELLOW}No snapshot will be created${NC}"

    # Disable deletion protection
    echo -e "${YELLOW}Disabling deletion protection...${NC}"
    aws rds modify-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --no-deletion-protection \
        --apply-immediately > /dev/null
    echo -e "${GREEN}✓ Deletion protection disabled${NC}"

    # Wait a moment for the modification to take effect
    sleep 5

    # Delete without snapshot
    echo -e "${YELLOW}Deleting RDS instance (no snapshot)...${NC}"
    aws rds delete-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --skip-final-snapshot > /dev/null
    echo -e "${GREEN}✓ RDS instance deletion initiated${NC}"
fi

echo ""
echo -e "${YELLOW}Waiting for RDS instance to be deleted (5-10 minutes)...${NC}"
aws rds wait db-instance-deleted --db-instance-identifier "$RDS_INSTANCE_ID"
echo -e "${GREEN}✓ RDS instance deleted${NC}"

# Clear environment file
echo -e "${YELLOW}Clearing aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^RDS_ENDPOINT=.*|RDS_ENDPOINT=\"\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env cleared${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RDS Instance Destroyed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$create_snapshot" == "yes" ]; then
    echo -e "${GREEN}Final snapshot created: ${SNAPSHOT_ID}${NC}"
    echo -e "${YELLOW}To restore from snapshot:${NC}"
    echo -e "  aws rds restore-db-instance-from-db-snapshot \\"
    echo -e "    --db-instance-identifier ${RDS_INSTANCE_ID} \\"
    echo -e "    --db-snapshot-identifier ${SNAPSHOT_ID}"
    echo ""
fi
