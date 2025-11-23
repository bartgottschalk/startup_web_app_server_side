#!/bin/bash

##############################################################################
# Create AWS Secrets Manager Secret for Production Application
#
# This script creates a secret to store ALL production credentials:
# - Database Master: username (postgres), password (auto-generated 32 chars)
# - Database App: username (django_app), password (auto-generated 32 chars)
# - Django: SECRET_KEY (auto-generated 50 characters)
# - Stripe: secret_key, publishable_key (placeholders - must update manually)
# - Email: host, port, user, password (placeholders - must update manually)
#
# Security: Separate passwords for master (admin) and application users
# following the principle of least privilege.
#
# Usage: ./scripts/infra/create-secrets.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# AFTER CREATION: Update Stripe and Email credentials using AWS Console or CLI
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

# Generate secure random credentials
echo -e "${YELLOW}Generating secure credentials...${NC}"
MASTER_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
APP_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
DJANGO_SECRET_KEY=$(openssl rand -base64 64 | tr -d '/+=' | head -c 50)
echo -e "${GREEN}✓ Master password generated (32 characters)${NC}"
echo -e "${GREEN}✓ Application password generated (32 characters)${NC}"
echo -e "${GREEN}✓ Django SECRET_KEY generated (50 characters)${NC}"

# Create secret with ALL production credentials
echo -e "${YELLOW}Creating secret in AWS Secrets Manager...${NC}"
DB_SECRET_ARN=$(aws secretsmanager create-secret \
    --name "$DB_SECRET_NAME" \
    --description "All production credentials for StartupWebApp (Database, Django, Stripe, Email)" \
    --secret-string "{
        \"engine\": \"postgresql\",
        \"host\": \"PLACEHOLDER_WILL_BE_UPDATED_AFTER_RDS_CREATION\",
        \"port\": 5432,
        \"master_username\": \"postgres\",
        \"master_password\": \"${MASTER_PASSWORD}\",
        \"username\": \"django_app\",
        \"password\": \"${APP_PASSWORD}\",
        \"dbClusterIdentifier\": \"${RDS_INSTANCE_ID}\",
        \"django_secret_key\": \"${DJANGO_SECRET_KEY}\",
        \"stripe_secret_key\": \"sk_live_PLACEHOLDER_UPDATE_WITH_REAL_KEY\",
        \"stripe_publishable_key\": \"pk_live_PLACEHOLDER_UPDATE_WITH_REAL_KEY\",
        \"email_host\": \"smtp.example.com\",
        \"email_port\": 587,
        \"email_user\": \"notifications@example.com\",
        \"email_password\": \"PLACEHOLDER_UPDATE_WITH_REAL_PASSWORD\"
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
echo -e "  Secret Name:         ${DB_SECRET_NAME}"
echo -e "  Secret ARN:          ${DB_SECRET_ARN}"
echo ""
echo -e "${GREEN}Auto-Generated (Secure):${NC}"
echo -e "  Master Username:     postgres"
echo -e "  Master Password:     [HIDDEN - 32 chars, stored in Secrets Manager]"
echo -e "  App Username:        django_app"
echo -e "  App Password:        [HIDDEN - 32 chars, stored in Secrets Manager]"
echo -e "  Django SECRET_KEY:   [HIDDEN - 50 chars, stored in Secrets Manager]"
echo ""
echo -e "${YELLOW}Placeholders (Must Update Manually):${NC}"
echo -e "  DB Host:             [Will be updated after RDS creation]"
echo -e "  Stripe Keys:         [Update with real sk_live_* and pk_live_* keys]"
echo -e "  Email Credentials:   [Update with real SMTP credentials]"
echo ""
echo -e "${YELLOW}⚠️  ACTION REQUIRED:${NC}"
echo -e "  1. Update Stripe keys (production keys start with sk_live_* and pk_live_*)"
echo -e "  2. Update Email credentials (SMTP host, user, password)"
echo ""
echo -e "${GREEN}To update secret values:${NC}"
echo -e "  # Via AWS Console:"
echo -e "    https://console.aws.amazon.com/secretsmanager/"
echo ""
echo -e "  # Via AWS CLI:"
echo -e "    aws secretsmanager update-secret --secret-id ${DB_SECRET_NAME} \\"
echo -e "      --secret-string '{\"stripe_secret_key\":\"sk_live_YOUR_KEY\",...}'"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Update Stripe and Email credentials in Secrets Manager"
echo -e "  2. Run: ./scripts/infra/create-rds.sh"
echo -e "  3. The RDS script will automatically update the 'host' field"
echo ""
