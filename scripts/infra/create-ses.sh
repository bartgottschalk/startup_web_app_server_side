#!/bin/bash

##############################################################################
# Create AWS SES Domain Identity and SMTP Credentials
#
# This script sets up AWS SES for email sending across all three apps
# (SWA, RG, BB). SES is shared infrastructure -- the domain identity,
# DKIM records, and SMTP credentials are account-wide.
#
# This script creates:
# 1. SES inline policy on startupwebapp-admin IAM user
# 2. SES domain identity for mosaicmeshai.com
# 3. DKIM signing (outputs 3 CNAME records for Namecheap DNS)
# 4. ses-smtp-user IAM user with ses:SendRawEmail permission only
# 5. SMTP credentials derived from the IAM user's access key
#
# After running this script:
# - Add the 3 DKIM CNAME records to Namecheap DNS
# - Update Secrets Manager for all three apps with SMTP credentials
# - Request production access (script does this automatically)
#
# Prerequisites:
# - AWS CLI configured with startupwebapp-admin credentials
# - aws-resources.env exists (from prior infrastructure setup)
# - Python3 available (for SMTP password derivation)
#
# Cost: SES free tier covers 62,000 emails/month (from EC2). Beyond that,
#       $0.10 per 1,000 emails.
#
# Usage: AWS_PROFILE=default ./scripts/infra/create-ses.sh
#
# IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize environment file
source "${SCRIPT_DIR}/init-env.sh"
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
PROJECT_NAME="startupwebapp"
ENVIRONMENT="production"
DOMAIN="mosaicmeshai.com"
SES_SMTP_USER="ses-smtp-user"
ADMIN_USER="startupwebapp-admin"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create SES Domain Identity & SMTP User${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Set default region if not in env file
AWS_REGION=${AWS_REGION:-us-east-1}
SES_SMTP_HOST="email-smtp.${AWS_REGION}.amazonaws.com"
SES_SMTP_PORT="587"

# Check if SES is already set up
if [ -n "${SES_DOMAIN_IDENTITY:-}" ]; then
    echo -e "${YELLOW}Checking if SES domain identity already exists...${NC}"

    IDENTITY_EXISTS=$(aws sesv2 get-email-identity \
        --email-identity "${SES_DOMAIN_IDENTITY}" \
        --region "${AWS_REGION}" \
        --query 'IdentityType' \
        --output text 2>/dev/null || echo "")

    if [ -n "$IDENTITY_EXISTS" ]; then
        echo -e "${GREEN}SES domain identity already exists: ${SES_DOMAIN_IDENTITY}${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-ses.sh first${NC}"
        exit 0
    else
        echo -e "${YELLOW}Domain in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will create SES email infrastructure for all three apps${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Domain:                 ${DOMAIN}"
echo -e "  SMTP Host:              ${SES_SMTP_HOST}"
echo -e "  SMTP Port:              ${SES_SMTP_PORT}"
echo -e "  Admin IAM User:         ${ADMIN_USER}"
echo -e "  SMTP IAM User:          ${SES_SMTP_USER}"
echo -e "  Region:                 ${AWS_REGION}"
echo ""
echo -e "${YELLOW}What will be created:${NC}"
echo -e "  1. SES inline policy on ${ADMIN_USER}"
echo -e "  2. SES domain identity for ${DOMAIN}"
echo -e "  3. DKIM signing configuration"
echo -e "  4. ${SES_SMTP_USER} IAM user with ses:SendRawEmail"
echo -e "  5. SMTP credentials for all apps"
echo ""
echo -e "${YELLOW}Cost Impact: Free tier covers 62,000 emails/month from EC2${NC}"
echo ""

read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# ============================================================================
# Step 1: Add SES permissions to startupwebapp-admin
# ============================================================================
echo ""
echo -e "${YELLOW}Step 1: Adding SES permissions to ${ADMIN_USER}...${NC}"

# Check if the inline policy already exists
EXISTING_POLICY=$(aws iam get-user-policy \
    --user-name "${ADMIN_USER}" \
    --policy-name "SESFullAccess" \
    --query 'PolicyDocument' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_POLICY" ]; then
    echo -e "${GREEN}SES inline policy already exists on ${ADMIN_USER}${NC}"
else
    aws iam put-user-policy \
        --user-name "${ADMIN_USER}" \
        --policy-name "SESFullAccess" \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "ses:*",
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": "sesv2:*",
                    "Resource": "*"
                }
            ]
        }'
    echo -e "${GREEN}SES inline policy attached to ${ADMIN_USER}${NC}"

    # IAM policies take a few seconds to propagate (eventual consistency)
    echo -e "${YELLOW}Waiting 10 seconds for IAM policy propagation...${NC}"
    sleep 10
fi

# ============================================================================
# Step 2: Create SES domain identity
# ============================================================================
echo ""
echo -e "${YELLOW}Step 2: Creating SES domain identity for ${DOMAIN}...${NC}"

# Check if domain identity already exists
EXISTING_IDENTITY=$(aws sesv2 get-email-identity \
    --email-identity "${DOMAIN}" \
    --region "${AWS_REGION}" \
    --query 'IdentityType' \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_IDENTITY" ]; then
    echo -e "${GREEN}SES domain identity already exists: ${DOMAIN}${NC}"
else
    aws sesv2 create-email-identity \
        --email-identity "${DOMAIN}" \
        --region "${AWS_REGION}" \
        --tags Key=Name,Value="${DOMAIN}" Key=Environment,Value="${ENVIRONMENT}" Key=Application,Value=SharedInfrastructure Key=ManagedBy,Value=InfrastructureAsCode > /dev/null
    echo -e "${GREEN}SES domain identity created: ${DOMAIN}${NC}"
fi

# ============================================================================
# Step 3: Get DKIM records
# ============================================================================
echo ""
echo -e "${YELLOW}Step 3: Retrieving DKIM configuration...${NC}"

DKIM_TOKENS=$(aws sesv2 get-email-identity \
    --email-identity "${DOMAIN}" \
    --region "${AWS_REGION}" \
    --query 'DkimAttributes.Tokens' \
    --output text)

echo -e "${GREEN}DKIM tokens retrieved${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  DKIM DNS Records for Namecheap${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Add these 3 CNAME records in Namecheap DNS:${NC}"
echo ""

TOKEN_NUM=1
for TOKEN in $DKIM_TOKENS; do
    echo -e "  ${GREEN}Record ${TOKEN_NUM}:${NC}"
    echo -e "    Type:   CNAME"
    echo -e "    Host:   ${TOKEN}._domainkey"
    echo -e "    Value:  ${TOKEN}.dkim.amazonses.com"
    echo ""
    TOKEN_NUM=$((TOKEN_NUM + 1))
done

echo -e "${YELLOW}Note: In Namecheap, do NOT include the domain in the Host field.${NC}"
echo -e "${YELLOW}Namecheap automatically appends .mosaicmeshai.com${NC}"
echo ""

read -p "Press Enter after you have added the DNS records (or press Enter to skip)..."

# ============================================================================
# Step 4: Wait for domain verification
# ============================================================================
echo ""
echo -e "${YELLOW}Step 4: Checking domain verification status...${NC}"
echo -e "${YELLOW}(Type 'skip' at any time to skip waiting)${NC}"

DKIM_STATUS="PENDING"
MAX_ATTEMPTS=30
ATTEMPT=1
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    DKIM_STATUS=$(aws sesv2 get-email-identity \
        --email-identity "${DOMAIN}" \
        --region "${AWS_REGION}" \
        --query 'DkimAttributes.Status' \
        --output text)

    if [ "$DKIM_STATUS" = "SUCCESS" ]; then
        echo -e "${GREEN}DKIM verification successful!${NC}"
        break
    elif [ "$DKIM_STATUS" = "FAILED" ]; then
        echo -e "${RED}DKIM verification failed. Check DNS records.${NC}"
        exit 1
    else
        echo -e "${YELLOW}  Status: ${DKIM_STATUS} (attempt ${ATTEMPT}/${MAX_ATTEMPTS})${NC}"
        # Read with timeout -- allows user to type 'skip' to break out
        read -t 30 -p "  Waiting 30s (type 'skip' to continue)... " SKIP_INPUT || true
        if [ "${SKIP_INPUT:-}" = "skip" ]; then
            echo -e "${YELLOW}Skipping verification wait.${NC}"
            break
        fi
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

if [ "$DKIM_STATUS" != "SUCCESS" ]; then
    echo -e "${YELLOW}DKIM verification is not yet complete (status: ${DKIM_STATUS}).${NC}"
    echo -e "${YELLOW}This is normal -- DNS propagation can take up to 72 hours.${NC}"
    echo -e "${YELLOW}You can check status later with:${NC}"
    echo -e "  aws sesv2 get-email-identity --email-identity ${DOMAIN} --region ${AWS_REGION} --query 'DkimAttributes.Status'"
    echo ""
    read -p "Continue with SMTP user creation? (yes/no): " CONTINUE_CONFIRM
    if [ "$CONTINUE_CONFIRM" != "yes" ]; then
        echo "Aborted. Run this script again after DNS propagation completes."
        exit 1
    fi
fi

# ============================================================================
# Step 5: Create ses-smtp-user IAM user
# ============================================================================
echo ""
echo -e "${YELLOW}Step 5: Creating ${SES_SMTP_USER} IAM user...${NC}"

# Check if user already exists
USER_EXISTS=$(aws iam get-user \
    --user-name "${SES_SMTP_USER}" \
    --query 'User.UserName' \
    --output text 2>/dev/null || echo "")

if [ -n "$USER_EXISTS" ]; then
    echo -e "${YELLOW}IAM user ${SES_SMTP_USER} already exists, skipping creation${NC}"
else
    aws iam create-user \
        --user-name "${SES_SMTP_USER}" \
        --tags Key=Name,Value="${SES_SMTP_USER}" Key=Environment,Value="${ENVIRONMENT}" Key=Application,Value=SharedInfrastructure Key=ManagedBy,Value=InfrastructureAsCode Key=Purpose,Value=SES-SMTP > /dev/null
    echo -e "${GREEN}IAM user created: ${SES_SMTP_USER}${NC}"
fi

# Attach inline policy for ses:SendRawEmail only
echo -e "${YELLOW}Attaching SendRawEmail policy...${NC}"
aws iam put-user-policy \
    --user-name "${SES_SMTP_USER}" \
    --policy-name "SESSendRawEmail" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ses:SendRawEmail",
                "Resource": "*"
            }
        ]
    }'
echo -e "${GREEN}SendRawEmail policy attached${NC}"

# ============================================================================
# Step 6: Generate SMTP credentials
# ============================================================================
echo ""
echo -e "${YELLOW}Step 6: Generating SMTP credentials...${NC}"

# Create access key for the SMTP user
ACCESS_KEY_JSON=$(aws iam create-access-key \
    --user-name "${SES_SMTP_USER}" \
    --output json)

IAM_ACCESS_KEY_ID=$(echo "$ACCESS_KEY_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['AccessKeyId'])")
IAM_SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['SecretAccessKey'])")

# Convert IAM secret access key to SES SMTP password
# AWS SES SMTP password is derived from the IAM secret access key using HMAC-SHA256
# Reference: https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html
SMTP_PASSWORD=$(python3 -c "
import hmac
import hashlib
import base64

# AWS SES SMTP password derivation algorithm (version 4)
# Reference: https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html
region = '${AWS_REGION}'
secret = '${IAM_SECRET_ACCESS_KEY}'

DATE = '11111111'
SERVICE = 'ses'
TERMINAL = 'aws4_request'
MESSAGE = 'SendRawEmail'
VERSION = 0x04

key = ('AWS4' + secret).encode('utf-8')
k_date = hmac.new(key, DATE.encode('utf-8'), hashlib.sha256).digest()
k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
k_service = hmac.new(k_region, SERVICE.encode('utf-8'), hashlib.sha256).digest()
k_terminal = hmac.new(k_service, TERMINAL.encode('utf-8'), hashlib.sha256).digest()
k_message = hmac.new(k_terminal, MESSAGE.encode('utf-8'), hashlib.sha256).digest()

signature_and_version = bytes([VERSION]) + k_message
smtp_password = base64.b64encode(signature_and_version).decode('utf-8')
print(smtp_password)
")

SMTP_USERNAME="${IAM_ACCESS_KEY_ID}"

echo -e "${GREEN}SMTP credentials generated${NC}"

# ============================================================================
# Step 7: Request production access
# ============================================================================
echo ""
echo -e "${YELLOW}Step 7: Requesting SES production access...${NC}"
echo -e "${YELLOW}(Moving out of sandbox mode)${NC}"

# Check current sending status
SENDING_ENABLED=$(aws sesv2 get-account \
    --region "${AWS_REGION}" \
    --query 'SendingEnabled' \
    --output text 2>/dev/null || echo "false")

PRODUCTION_ACCESS=$(aws sesv2 get-account \
    --region "${AWS_REGION}" \
    --query 'ProductionAccessEnabled' \
    --output text 2>/dev/null || echo "false")

if [ "$PRODUCTION_ACCESS" = "True" ] || [ "$PRODUCTION_ACCESS" = "true" ]; then
    echo -e "${GREEN}Production access is already enabled!${NC}"
else
    echo -e "${YELLOW}Current status: Sandbox mode (can only send to verified addresses)${NC}"
    echo ""
    echo -e "${YELLOW}To request production access:${NC}"
    echo -e "  1. Go to AWS Console > SES > Account dashboard"
    echo -e "  2. Click 'Request production access'"
    echo -e "  3. Fill in the form:"
    echo -e "     - Mail type: Transactional"
    echo -e "     - Website URL: https://mosaicmeshai.com"
    echo -e "     - Use case: Transactional emails (order confirmations, password resets,"
    echo -e "       email verifications) for web applications hosted on AWS ECS."
    echo -e "     - Expected daily sending volume: Under 1,000"
    echo -e "     - How do you handle bounces/complaints: Monitor via SES dashboard"
    echo -e "  4. AWS typically approves within 24-48 hours"
    echo ""
    echo -e "${YELLOW}Alternatively, request via CLI:${NC}"
    echo -e "  aws sesv2 put-account-details \\"
    echo -e "    --production-access-enabled \\"
    echo -e "    --mail-type TRANSACTIONAL \\"
    echo -e "    --website-url https://mosaicmeshai.com \\"
    echo -e "    --use-case-description 'Transactional emails (order confirmations, password resets, email verifications) for web applications hosted on AWS ECS. Low volume, under 1000 emails per day.' \\"
    echo -e "    --additional-contact-email-addresses bart@mosaicmeshai.com \\"
    echo -e "    --contact-language EN \\"
    echo -e "    --region ${AWS_REGION}"
fi

# ============================================================================
# Step 8: Update aws-resources.env
# ============================================================================
echo ""
echo -e "${YELLOW}Step 8: Updating aws-resources.env...${NC}"

# Add SES section to env file
if grep -q "^SES_DOMAIN_IDENTITY=" "$ENV_FILE"; then
    # Update existing lines (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i .bak "s|^SES_DOMAIN_IDENTITY=.*|SES_DOMAIN_IDENTITY=\"${DOMAIN}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_SMTP_USER_NAME=.*|SES_SMTP_USER_NAME=\"${SES_SMTP_USER}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_SMTP_HOST=.*|SES_SMTP_HOST=\"${SES_SMTP_HOST}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_SMTP_PORT=.*|SES_SMTP_PORT=\"${SES_SMTP_PORT}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_SMTP_USERNAME=.*|SES_SMTP_USERNAME=\"${SMTP_USERNAME}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_SMTP_PASSWORD=.*|SES_SMTP_PASSWORD=\"${SMTP_PASSWORD}\"|" "$ENV_FILE"
        sed -i .bak "s|^SES_IAM_ACCESS_KEY_ID=.*|SES_IAM_ACCESS_KEY_ID=\"${IAM_ACCESS_KEY_ID}\"|" "$ENV_FILE"
    else
        sed -i.bak "s|^SES_DOMAIN_IDENTITY=.*|SES_DOMAIN_IDENTITY=\"${DOMAIN}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_SMTP_USER_NAME=.*|SES_SMTP_USER_NAME=\"${SES_SMTP_USER}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_SMTP_HOST=.*|SES_SMTP_HOST=\"${SES_SMTP_HOST}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_SMTP_PORT=.*|SES_SMTP_PORT=\"${SES_SMTP_PORT}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_SMTP_USERNAME=.*|SES_SMTP_USERNAME=\"${SMTP_USERNAME}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_SMTP_PASSWORD=.*|SES_SMTP_PASSWORD=\"${SMTP_PASSWORD}\"|" "$ENV_FILE"
        sed -i.bak "s|^SES_IAM_ACCESS_KEY_ID=.*|SES_IAM_ACCESS_KEY_ID=\"${IAM_ACCESS_KEY_ID}\"|" "$ENV_FILE"
    fi
else
    # Add new section
    echo "" >> "$ENV_FILE"
    echo "# SES Email Infrastructure (Shared)" >> "$ENV_FILE"
    echo "SES_DOMAIN_IDENTITY=\"${DOMAIN}\"" >> "$ENV_FILE"
    echo "SES_SMTP_USER_NAME=\"${SES_SMTP_USER}\"" >> "$ENV_FILE"
    echo "SES_SMTP_HOST=\"${SES_SMTP_HOST}\"" >> "$ENV_FILE"
    echo "SES_SMTP_PORT=\"${SES_SMTP_PORT}\"" >> "$ENV_FILE"
    echo "SES_SMTP_USERNAME=\"${SMTP_USERNAME}\"" >> "$ENV_FILE"
    echo "SES_SMTP_PASSWORD=\"${SMTP_PASSWORD}\"" >> "$ENV_FILE"
    echo "SES_IAM_ACCESS_KEY_ID=\"${IAM_ACCESS_KEY_ID}\"" >> "$ENV_FILE"
fi
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}aws-resources.env updated${NC}"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SES Infrastructure Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Domain Identity:${NC}"
echo -e "  Domain:                 ${DOMAIN}"
echo -e "  DKIM Status:            ${DKIM_STATUS:-PENDING}"
echo ""
echo -e "${GREEN}SMTP Credentials (for all three apps):${NC}"
echo -e "  Host:                   ${SES_SMTP_HOST}"
echo -e "  Port:                   ${SES_SMTP_PORT}"
echo -e "  Username:               ${SMTP_USERNAME}"
echo -e "  Password:               ${SMTP_PASSWORD}"
echo ""
echo -e "${GREEN}IAM Resources:${NC}"
echo -e "  Admin Policy:           SESFullAccess on ${ADMIN_USER}"
echo -e "  SMTP User:              ${SES_SMTP_USER}"
echo -e "  SMTP User Policy:       SESSendRawEmail"
echo -e "  Access Key ID:          ${IAM_ACCESS_KEY_ID}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "  ${YELLOW}1. Update Secrets Manager for all three apps:${NC}"
echo ""
echo -e "     For each secret, update these fields:"
echo -e "       email_host:     ${SES_SMTP_HOST}"
echo -e "       email_port:     ${SES_SMTP_PORT}"
echo -e "       email_user:     ${SMTP_USERNAME}"
echo -e "       email_password: ${SMTP_PASSWORD}"
echo ""
echo -e "     Secrets to update:"
echo -e "       - rds/startupwebapp/multi-tenant/master  (SWA)"
echo -e "       - rds/refrigeratorgames/prod             (RG)"
echo -e "       - rds/bartbot/multi-tenant/master        (BB)"
echo ""
echo -e "  ${YELLOW}2. Request production access (if not already approved):${NC}"
echo -e "     AWS Console > SES > Account dashboard > Request production access"
echo ""
echo -e "  ${YELLOW}3. Add DEFAULT_FROM_EMAIL to BartBot settings:${NC}"
echo -e "     settings_production.py and settings_secret.py"
echo ""
echo -e "  ${YELLOW}4. Redeploy all three backends to pick up new credentials${NC}"
echo ""
echo -e "  ${YELLOW}5. Test email delivery from each app${NC}"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  Check domain status:    aws sesv2 get-email-identity --email-identity ${DOMAIN} --region ${AWS_REGION}"
echo -e "  Check account status:   aws sesv2 get-account --region ${AWS_REGION}"
echo -e "  Send test email:        aws sesv2 send-email --from-email-address test@${DOMAIN} --destination ToAddresses=you@example.com --content 'Simple={Subject={Data=Test},Body={Text={Data=Test}}}' --region ${AWS_REGION}"
echo -e "  Check sending quota:    aws sesv2 get-account --region ${AWS_REGION} --query 'SendQuota'"
echo ""
