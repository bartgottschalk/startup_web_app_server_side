#!/bin/bash

##############################################################################
# Create ACM Certificate for StartupWebApp
#
# This script creates:
# - ACM certificate for *.mosaicmeshai.com (wildcard)
# - DNS validation records (to be added manually in Namecheap)
#
# Why Wildcard Certificate?
# - Covers: startupwebapp-api.mosaicmeshai.com (backend API)
# - Covers: startupwebapp.mosaicmeshai.com (frontend)
# - Covers: Any future subdomains
# - One certificate for all services
#
# DNS Validation:
# - AWS provides a CNAME record to add in Namecheap
# - Validation typically takes 5-30 minutes after DNS propagation
# - Certificate remains valid for 13 months (auto-renews if DNS record exists)
#
# Cost: $0 (ACM certificates are free for use with AWS services)
#
# Usage: ./scripts/infra/create-acm-certificate.sh
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

# Certificate configuration
DOMAIN_NAME="*.mosaicmeshai.com"
SUBJECT_ALTERNATIVE_NAMES="mosaicmeshai.com"  # Also cover root domain

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create ACM Certificate${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check if certificate already exists
if [ -n "${ACM_CERTIFICATE_ARN:-}" ]; then
    echo -e "${YELLOW}Checking if certificate exists...${NC}"
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "${ACM_CERTIFICATE_ARN}" \
        --region "${AWS_REGION}" \
        --query 'Certificate.Status' \
        --output text 2>/dev/null || echo "")

    if [ -n "$CERT_STATUS" ]; then
        echo -e "${GREEN}✓ Certificate already exists: ${ACM_CERTIFICATE_ARN}${NC}"
        echo -e "  Status: ${CERT_STATUS}"

        if [ "$CERT_STATUS" == "PENDING_VALIDATION" ]; then
            echo ""
            echo -e "${YELLOW}Certificate is pending DNS validation.${NC}"
            echo -e "${YELLOW}Add the following CNAME record in Namecheap:${NC}"
            echo ""

            # Get validation records
            aws acm describe-certificate \
                --certificate-arn "${ACM_CERTIFICATE_ARN}" \
                --region "${AWS_REGION}" \
                --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord.Name,ResourceRecord.Value]' \
                --output text | while read -r domain name value; do
                echo -e "  Domain: ${domain}"
                echo -e "  ${GREEN}CNAME Name:  ${name}${NC}"
                echo -e "  ${GREEN}CNAME Value: ${value}${NC}"
                echo ""
            done
        fi

        echo -e "${YELLOW}To delete and recreate, run: ./scripts/infra/destroy-acm-certificate.sh${NC}"
        exit 0
    else
        echo -e "${YELLOW}Certificate ARN in env file but not found in AWS, creating new...${NC}"
    fi
fi

echo -e "${YELLOW}This will request an SSL/TLS certificate for:${NC}"
echo -e "  Primary domain:     ${DOMAIN_NAME}"
echo -e "  Additional domain:  ${SUBJECT_ALTERNATIVE_NAMES}"
echo ""
echo -e "${YELLOW}Subdomains covered:${NC}"
echo -e "  - startupwebapp-api.mosaicmeshai.com (backend API)"
echo -e "  - startupwebapp.mosaicmeshai.com (frontend)"
echo -e "  - mosaicmeshai.com (root domain)"
echo -e "  - Any other *.mosaicmeshai.com subdomain"
echo ""
echo -e "${YELLOW}Validation method: DNS${NC}"
echo -e "${YELLOW}You will need to add a CNAME record in Namecheap.${NC}"
echo ""
echo -e "${YELLOW}Cost: \$0 (ACM certificates are free)${NC}"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Request certificate
echo ""
echo -e "${YELLOW}Step 1: Requesting ACM certificate...${NC}"

ACM_CERTIFICATE_ARN=$(aws acm request-certificate \
    --domain-name "${DOMAIN_NAME}" \
    --subject-alternative-names "${SUBJECT_ALTERNATIVE_NAMES}" \
    --validation-method DNS \
    --region "${AWS_REGION}" \
    --tags "Key=Name,Value=${PROJECT_NAME}-certificate" "Key=Environment,Value=${ENVIRONMENT}" "Key=Application,Value=StartupWebApp" "Key=ManagedBy,Value=InfrastructureAsCode" \
    --query 'CertificateArn' \
    --output text)

echo -e "${GREEN}✓ Certificate requested: ${ACM_CERTIFICATE_ARN}${NC}"

# Step 2: Wait for DNS validation records to be generated
echo ""
echo -e "${YELLOW}Step 2: Waiting for DNS validation records (10-15 seconds)...${NC}"
sleep 15

# Step 3: Get DNS validation records
echo ""
echo -e "${YELLOW}Step 3: Retrieving DNS validation records...${NC}"

# Get certificate details
CERT_DETAILS=$(aws acm describe-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}" \
    --output json)

CERT_STATUS=$(echo "$CERT_DETAILS" | jq -r '.Certificate.Status')
echo -e "  Certificate Status: ${CERT_STATUS}"

# Step 4: Save to env file
echo ""
echo -e "${YELLOW}Step 4: Updating aws-resources.env...${NC}"

sed -i.bak \
    -e "s|^ACM_CERTIFICATE_ARN=.*|ACM_CERTIFICATE_ARN=\"${ACM_CERTIFICATE_ARN}\"|" \
    "$ENV_FILE"
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}✓ aws-resources.env updated${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ACM Certificate Requested${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Certificate ARN:${NC}"
echo -e "  ${ACM_CERTIFICATE_ARN}"
echo ""
echo -e "${GREEN}Status: ${CERT_STATUS}${NC}"
echo ""

# Display DNS validation records
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  ACTION REQUIRED: Add DNS Record in Namecheap${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Add the following CNAME record(s) in Namecheap DNS:${NC}"
echo ""

# Parse and display validation records
echo "$CERT_DETAILS" | jq -r '.Certificate.DomainValidationOptions[] | "Domain: \(.DomainName)\nCNAME Name:  \(.ResourceRecord.Name)\nCNAME Value: \(.ResourceRecord.Value)\n"'

echo ""
echo -e "${YELLOW}Steps to add in Namecheap:${NC}"
echo -e "  1. Log in to Namecheap: https://www.namecheap.com"
echo -e "  2. Go to Domain List → mosaicmeshai.com → Manage"
echo -e "  3. Click 'Advanced DNS' tab"
echo -e "  4. Add New Record → Type: CNAME Record"
echo -e "  5. Host: Copy the CNAME Name (without .mosaicmeshai.com)"
echo -e "  6. Value: Copy the CNAME Value"
echo -e "  7. TTL: Automatic"
echo -e "  8. Click the checkmark to save"
echo ""
echo -e "${YELLOW}IMPORTANT: The CNAME Name from AWS includes the full domain.${NC}"
echo -e "${YELLOW}In Namecheap, you only enter the HOST portion (before .mosaicmeshai.com)${NC}"
echo ""
echo -e "${YELLOW}Example:${NC}"
echo -e "  AWS gives:      _abc123def456.mosaicmeshai.com."
echo -e "  Namecheap Host: _abc123def456"
echo ""
echo -e "${GREEN}After adding DNS record:${NC}"
echo -e "  - Wait 5-30 minutes for DNS propagation"
echo -e "  - Certificate will auto-validate once AWS sees the CNAME"
echo -e "  - Check status: ./scripts/infra/status.sh"
echo ""
echo -e "${GREEN}Verify certificate status:${NC}"
echo -e "  aws acm describe-certificate \\"
echo -e "    --certificate-arn ${ACM_CERTIFICATE_ARN} \\"
echo -e "    --query 'Certificate.Status' --output text"
echo ""
echo -e "${GREEN}Once validated (status = ISSUED):${NC}"
echo -e "  Run: ./scripts/infra/create-alb-https-listener.sh"
echo ""
echo -e "${YELLOW}Phase 5.15 Progress:${NC}"
echo -e "  ✓ Step 1: Create Application Load Balancer (ALB)"
echo -e "  ✓ Step 2: Request ACM Certificate"
echo -e "  → Next: Step 3 - Configure Namecheap DNS (manual)"
echo ""
