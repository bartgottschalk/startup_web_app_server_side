#!/bin/bash

##############################################################################
# Destroy AWS SES Domain Identity and SMTP Credentials
#
# This script removes all SES infrastructure:
# 1. ses-smtp-user IAM user (policies, access keys, then user)
# 2. SES domain identity (mosaicmeshai.com)
# 3. SES inline policy from startupwebapp-admin
# 4. Clears SES entries from aws-resources.env
#
# After running this script:
# - All three apps will lose email sending capability until SES is recreated
#   or Secrets Manager entries are reverted to Gmail SMTP credentials
# - DKIM CNAME records in Namecheap can optionally be removed
#
# Usage: AWS_PROFILE=default ./scripts/infra/destroy-ses.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
# WARNING: This will break email sending for ALL three apps (SWA, RG, BB)
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
DOMAIN="mosaicmeshai.com"
SES_SMTP_USER="ses-smtp-user"
ADMIN_USER="startupwebapp-admin"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Destroying SES Infrastructure${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Source resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

AWS_REGION=${AWS_REGION:-us-east-1}

# Gather current state for display
echo -e "${YELLOW}Checking current SES resources...${NC}"
echo ""

DOMAIN_EXISTS=$(aws sesv2 get-email-identity \
    --email-identity "${DOMAIN}" \
    --region "${AWS_REGION}" \
    --query 'IdentityType' \
    --output text 2>/dev/null || echo "")

USER_EXISTS=$(aws iam get-user \
    --user-name "${SES_SMTP_USER}" \
    --query 'User.UserName' \
    --output text 2>/dev/null || echo "")

ADMIN_POLICY_EXISTS=$(aws iam get-user-policy \
    --user-name "${ADMIN_USER}" \
    --policy-name "SESFullAccess" \
    --query 'PolicyName' \
    --output text 2>/dev/null || echo "")

echo -e "${RED}WARNING: This will destroy ALL SES email infrastructure!${NC}"
echo -e "${RED}All three apps (SWA, RG, BB) will lose email sending capability.${NC}"
echo ""
echo -e "${YELLOW}Resources to be deleted:${NC}"
echo -e "  Domain Identity:        ${DOMAIN} (${DOMAIN_EXISTS:-not found})"
echo -e "  SMTP IAM User:          ${SES_SMTP_USER} (${USER_EXISTS:-not found})"
echo -e "  Admin SES Policy:       SESFullAccess on ${ADMIN_USER} (${ADMIN_POLICY_EXISTS:-not found})"
echo ""

read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Aborted.${NC}"
    exit 0
fi

# ============================================================================
# Step 1: Delete ses-smtp-user IAM user
# ============================================================================
echo ""
echo -e "${YELLOW}Step 1: Deleting ${SES_SMTP_USER} IAM user...${NC}"

if [ -n "$USER_EXISTS" ]; then
    # Remove inline policies
    echo -e "${YELLOW}  Removing inline policies...${NC}"
    POLICIES=$(aws iam list-user-policies \
        --user-name "${SES_SMTP_USER}" \
        --query 'PolicyNames' \
        --output text 2>/dev/null || echo "")

    for POLICY in $POLICIES; do
        aws iam delete-user-policy \
            --user-name "${SES_SMTP_USER}" \
            --policy-name "$POLICY" 2>/dev/null || true
        echo -e "${GREEN}    Removed policy: ${POLICY}${NC}"
    done

    # Remove access keys
    echo -e "${YELLOW}  Removing access keys...${NC}"
    ACCESS_KEYS=$(aws iam list-access-keys \
        --user-name "${SES_SMTP_USER}" \
        --query 'AccessKeyMetadata[].AccessKeyId' \
        --output text 2>/dev/null || echo "")

    for KEY_ID in $ACCESS_KEYS; do
        aws iam delete-access-key \
            --user-name "${SES_SMTP_USER}" \
            --access-key-id "$KEY_ID" 2>/dev/null || true
        echo -e "${GREEN}    Removed access key: ${KEY_ID}${NC}"
    done

    # Delete user
    echo -e "${YELLOW}  Deleting IAM user...${NC}"
    aws iam delete-user \
        --user-name "${SES_SMTP_USER}" 2>/dev/null || true
    echo -e "${GREEN}  ${SES_SMTP_USER} deleted${NC}"
else
    echo -e "${YELLOW}  IAM user ${SES_SMTP_USER} not found, skipping${NC}"
fi

# ============================================================================
# Step 2: Delete SES domain identity
# ============================================================================
echo ""
echo -e "${YELLOW}Step 2: Deleting SES domain identity for ${DOMAIN}...${NC}"

if [ -n "$DOMAIN_EXISTS" ]; then
    aws sesv2 delete-email-identity \
        --email-identity "${DOMAIN}" \
        --region "${AWS_REGION}" 2>/dev/null || true
    echo -e "${GREEN}  Domain identity deleted: ${DOMAIN}${NC}"
else
    echo -e "${YELLOW}  Domain identity ${DOMAIN} not found, skipping${NC}"
fi

# ============================================================================
# Step 3: Remove SES inline policy from startupwebapp-admin
# ============================================================================
echo ""
echo -e "${YELLOW}Step 3: Removing SES policy from ${ADMIN_USER}...${NC}"

if [ -n "$ADMIN_POLICY_EXISTS" ]; then
    aws iam delete-user-policy \
        --user-name "${ADMIN_USER}" \
        --policy-name "SESFullAccess" 2>/dev/null || true
    echo -e "${GREEN}  SESFullAccess policy removed from ${ADMIN_USER}${NC}"
else
    echo -e "${YELLOW}  SESFullAccess policy not found on ${ADMIN_USER}, skipping${NC}"
fi

# ============================================================================
# Step 4: Clear SES entries from aws-resources.env
# ============================================================================
echo ""
echo -e "${YELLOW}Step 4: Clearing SES entries from aws-resources.env...${NC}"

if grep -q "^SES_DOMAIN_IDENTITY=" "$ENV_FILE" 2>/dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak \
            -e '/^# SES Email Infrastructure/d' \
            -e '/^SES_DOMAIN_IDENTITY=/d' \
            -e '/^SES_SMTP_USER_NAME=/d' \
            -e '/^SES_SMTP_HOST=/d' \
            -e '/^SES_SMTP_PORT=/d' \
            -e '/^SES_SMTP_USERNAME=/d' \
            -e '/^SES_SMTP_PASSWORD=/d' \
            -e '/^SES_IAM_ACCESS_KEY_ID=/d' \
            "$ENV_FILE"
    else
        sed -i.bak \
            -e '/^# SES Email Infrastructure/d' \
            -e '/^SES_DOMAIN_IDENTITY=/d' \
            -e '/^SES_SMTP_USER_NAME=/d' \
            -e '/^SES_SMTP_HOST=/d' \
            -e '/^SES_SMTP_PORT=/d' \
            -e '/^SES_SMTP_USERNAME=/d' \
            -e '/^SES_SMTP_PASSWORD=/d' \
            -e '/^SES_IAM_ACCESS_KEY_ID=/d' \
            "$ENV_FILE"
    fi
    rm -f "${ENV_FILE}.bak"
    echo -e "${GREEN}  SES entries cleared from aws-resources.env${NC}"
else
    echo -e "${YELLOW}  No SES entries found in aws-resources.env, skipping${NC}"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SES Infrastructure Destroyed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Deleted:${NC}"
echo -e "  SES domain identity:    ${DOMAIN}"
echo -e "  IAM user:               ${SES_SMTP_USER}"
echo -e "  Admin SES policy:       SESFullAccess on ${ADMIN_USER}"
echo -e "  Env file entries:       Cleared"
echo ""
echo -e "${YELLOW}Optional: Remove DKIM CNAME records from Namecheap DNS${NC}"
echo -e "${YELLOW}(These are harmless to leave in place)${NC}"
echo ""
echo -e "${YELLOW}To restore email sending:${NC}"
echo -e "  Option A: Recreate SES:  ./scripts/infra/create-ses.sh"
echo -e "  Option B: Revert to Gmail by updating Secrets Manager entries"
echo -e "            with the original Gmail SMTP credentials"
echo ""
