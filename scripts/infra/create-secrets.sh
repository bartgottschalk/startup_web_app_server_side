#!/bin/bash

##############################################################################
# Create AWS Secrets Manager Secret for RDS Credentials
#
# This script creates a secret to store RDS database credentials:
# - Username: django_app
# - Password: Auto-generated secure password
# - Host: Will be updated after RDS is created
# - Port: 5432
#
# Usage: ./scripts/infra/create-secrets.sh
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
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Creating Secrets Manager Secret${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if secret already exists
if [ -n "${DB_SECRET_ARN:-}" ]; then
    echo -e "${YELLOW}Secret already exists: ${DB_SECRET_NAME}${NC}"
    echo -e "${YELLOW}ARN: ${DB_SECRET_ARN}${NC}"
    echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-secrets.sh first${NC}"
    exit 0
fi

# Generate secure random password (32 characters, alphanumeric + special chars)
echo -e "${YELLOW}Generating secure password...${NC}"
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo -e "${GREEN}✓ Secure password generated (32 characters)${NC}"

# Create secret (host will be updated after RDS is created)
echo -e "${YELLOW}Creating secret in AWS Secrets Manager...${NC}"
DB_SECRET_ARN=$(aws secretsmanager create-secret \
    --name "$DB_SECRET_NAME" \
    --description "PostgreSQL credentials for StartupWebApp multi-tenant RDS instance" \
    --secret-string "{
        \"engine\": \"postgresql\",
        \"host\": \"PLACEHOLDER_WILL_BE_UPDATED_AFTER_RDS_CREATION\",
        \"port\": 5432,
        \"username\": \"django_app\",
        \"password\": \"${DB_PASSWORD}\",
        \"dbClusterIdentifier\": \"${RDS_INSTANCE_ID}\"
    }" \
    --tags "Key=Name,Value=${DB_SECRET_NAME}" \
           "Key=Environment,Value=${ENVIRONMENT}" \
           "Key=Application,Value=StartupWebApp" \
           "Key=ManagedBy,Value=InfrastructureAsCode" \
    --query 'ARN' \
    --output text)
echo -e "${GREEN}✓ Secret created: ${DB_SECRET_NAME}${NC}"
echo -e "${GREEN}✓ ARN: ${DB_SECRET_ARN}${NC}"

# Update environment file
echo -e "${YELLOW}Updating aws-resources.env...${NC}"
sed -i.bak \
    -e "s|^DB_SECRET_ARN=.*|DB_SECRET_ARN=\"${DB_SECRET_ARN}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"
echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Secret Created Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo -e "  Secret Name:    ${DB_SECRET_NAME}"
echo -e "  Secret ARN:     ${DB_SECRET_ARN}"
echo -e "  Username:       django_app"
echo -e "  Password:       [HIDDEN - stored in Secrets Manager]"
echo -e "  Host:           [Will be updated after RDS creation]"
echo -e "  Port:           5432"
echo ""
echo -e "${YELLOW}Note: The 'host' field is a placeholder and will be updated after RDS instance is created${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Run: ./scripts/infra/create-rds.sh"
echo -e "  2. The RDS script will automatically update the 'host' field in this secret"
echo ""
