#!/bin/bash

##############################################################################
# Create S3 + CloudFront Frontend Hosting for StartupWebApp
#
# This script creates:
# - S3 bucket for static frontend files
# - CloudFront Origin Access Control (OAC) for secure S3 access
# - CloudFront distribution with ACM certificate
# - S3 bucket policy allowing only CloudFront access
#
# Architecture:
#   Users -> CloudFront (HTTPS) -> S3 (private)
#
# Why CloudFront + S3?
# - Global CDN for fast content delivery
# - HTTPS with ACM certificate (free)
# - S3 bucket remains private (no public access)
# - Cache control for performance (versioned JS/CSS cached 1 year)
# - Custom domain support (startupwebapp.mosaicmeshai.com)
#
# Prerequisites:
# - ACM certificate must exist (*.mosaicmeshai.com)
# - Run after: create-acm-certificate.sh
#
# Cost: ~$1-5/month (S3 storage + CloudFront requests)
#
# Usage: ./scripts/infra/create-frontend-hosting.sh
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

# S3 and CloudFront configuration
BUCKET_NAME="${PROJECT_NAME}-frontend-${ENVIRONMENT}"
CLOUDFRONT_COMMENT="StartupWebApp Frontend Distribution"
CUSTOM_DOMAIN="startupwebapp.mosaicmeshai.com"
OAC_NAME="${PROJECT_NAME}-frontend-oac"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Create S3 + CloudFront Frontend Hosting${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verify prerequisites
if [ -z "${ACM_CERTIFICATE_ARN:-}" ]; then
    echo -e "${RED}Error: ACM_CERTIFICATE_ARN not found in aws-resources.env${NC}"
    echo -e "${YELLOW}Please create ACM certificate first: ./scripts/infra/create-acm-certificate.sh${NC}"
    exit 1
fi

# Verify ACM certificate is issued
echo -e "${YELLOW}Verifying ACM certificate status...${NC}"
CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn "${ACM_CERTIFICATE_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Certificate.Status' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo -e "${RED}Error: ACM certificate is not in ISSUED state (current: ${CERT_STATUS})${NC}"
    echo -e "${YELLOW}Please ensure DNS validation is complete${NC}"
    exit 1
fi
echo -e "${GREEN}ACM certificate is valid${NC}"

# Check if S3 bucket already exists
BUCKET_EXISTS=$(aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>&1 || echo "NOT_FOUND")
if [[ "$BUCKET_EXISTS" != *"NOT_FOUND"* ]] && [[ "$BUCKET_EXISTS" != *"404"* ]] && [[ "$BUCKET_EXISTS" != *"Not Found"* ]]; then
    echo -e "${GREEN}S3 bucket already exists: ${BUCKET_NAME}${NC}"
    BUCKET_ALREADY_EXISTS=true
else
    BUCKET_ALREADY_EXISTS=false
fi

# Check if CloudFront distribution already exists
if [ -n "${CLOUDFRONT_DISTRIBUTION_ID:-}" ]; then
    echo -e "${YELLOW}Checking if CloudFront distribution exists...${NC}"
    CF_STATUS=$(aws cloudfront get-distribution \
        --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --query 'Distribution.Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")

    if [ "$CF_STATUS" != "NOT_FOUND" ]; then
        echo -e "${GREEN}CloudFront distribution already exists: ${CLOUDFRONT_DISTRIBUTION_ID} (${CF_STATUS})${NC}"
        echo -e "${YELLOW}To recreate, run ./scripts/infra/destroy-frontend-hosting.sh first${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  S3 Bucket:          ${BUCKET_NAME}"
echo -e "  Custom Domain:      ${CUSTOM_DOMAIN}"
echo -e "  ACM Certificate:    ${ACM_CERTIFICATE_ARN}"
echo -e "  OAC Name:           ${OAC_NAME}"
echo ""
echo -e "${YELLOW}This will create:${NC}"
echo -e "  1. S3 bucket for static files (private)"
echo -e "  2. CloudFront Origin Access Control"
echo -e "  3. CloudFront distribution with HTTPS"
echo -e "  4. S3 bucket policy for CloudFront access"
echo ""
echo -e "${YELLOW}Estimated Cost: ~\$1-5/month${NC}"
echo ""
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

echo ""

##############################################################################
# Step 1: Create S3 Bucket
##############################################################################

if [ "$BUCKET_ALREADY_EXISTS" = false ]; then
    echo -e "${YELLOW}Step 1: Creating S3 bucket...${NC}"

    # Create bucket (different command for us-east-1 vs other regions)
    if [ "${AWS_REGION}" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "${BUCKET_NAME}" \
            --region "${AWS_REGION}"
    else
        aws s3api create-bucket \
            --bucket "${BUCKET_NAME}" \
            --region "${AWS_REGION}" \
            --create-bucket-configuration LocationConstraint="${AWS_REGION}"
    fi

    echo -e "${GREEN}S3 bucket created: ${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}Step 1: S3 bucket already exists, skipping creation${NC}"
fi

# Block all public access (CloudFront will access via OAC)
echo -e "${YELLOW}Configuring bucket to block public access...${NC}"
aws s3api put-public-access-block \
    --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo -e "${GREEN}Public access blocked${NC}"

# Enable versioning for safety
echo -e "${YELLOW}Enabling bucket versioning...${NC}"
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled

echo -e "${GREEN}Versioning enabled${NC}"

##############################################################################
# Step 2: Create CloudFront Origin Access Control (OAC)
##############################################################################

echo ""
echo -e "${YELLOW}Step 2: Creating CloudFront Origin Access Control...${NC}"

# Check if OAC already exists
EXISTING_OAC_ID=$(aws cloudfront list-origin-access-controls \
    --query "OriginAccessControlList.Items[?Name=='${OAC_NAME}'].Id" \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_OAC_ID" ] && [ "$EXISTING_OAC_ID" != "None" ]; then
    echo -e "${GREEN}OAC already exists: ${EXISTING_OAC_ID}${NC}"
    OAC_ID="$EXISTING_OAC_ID"
else
    OAC_CONFIG=$(cat <<EOF
{
    "Name": "${OAC_NAME}",
    "Description": "OAC for StartupWebApp frontend S3 bucket",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
}
EOF
)

    OAC_RESULT=$(aws cloudfront create-origin-access-control \
        --origin-access-control-config "${OAC_CONFIG}")

    OAC_ID=$(echo "$OAC_RESULT" | jq -r '.OriginAccessControl.Id')
    echo -e "${GREEN}OAC created: ${OAC_ID}${NC}"
fi

##############################################################################
# Step 3: Create CloudFront Distribution
##############################################################################

echo ""
echo -e "${YELLOW}Step 3: Creating CloudFront distribution...${NC}"
echo -e "${YELLOW}(This may take 5-10 minutes to deploy globally)${NC}"

# Get AWS account ID for S3 bucket ARN
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

# Create distribution configuration
DISTRIBUTION_CONFIG=$(cat <<EOF
{
    "CallerReference": "startupwebapp-frontend-$(date +%s)",
    "Comment": "${CLOUDFRONT_COMMENT}",
    "Enabled": true,
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com",
                "OriginAccessControlId": "${OAC_ID}",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        "Compress": true
    },
    "CacheBehaviors": {
        "Quantity": 2,
        "Items": [
            {
                "PathPattern": "*.html",
                "TargetOriginId": "S3-${BUCKET_NAME}",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
                "Compress": true
            },
            {
                "PathPattern": "index.html",
                "TargetOriginId": "S3-${BUCKET_NAME}",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {
                        "Quantity": 2,
                        "Items": ["GET", "HEAD"]
                    }
                },
                "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
                "Compress": true
            }
        ]
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/error.html",
                "ResponseCode": "404",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "Aliases": {
        "Quantity": 1,
        "Items": ["${CUSTOM_DOMAIN}"]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": "${ACM_CERTIFICATE_ARN}",
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "HttpVersion": "http2and3",
    "PriceClass": "PriceClass_100"
}
EOF
)

DISTRIBUTION_RESULT=$(aws cloudfront create-distribution \
    --distribution-config "${DISTRIBUTION_CONFIG}")

CLOUDFRONT_DISTRIBUTION_ID=$(echo "$DISTRIBUTION_RESULT" | jq -r '.Distribution.Id')
CLOUDFRONT_DOMAIN_NAME=$(echo "$DISTRIBUTION_RESULT" | jq -r '.Distribution.DomainName')
CLOUDFRONT_ARN=$(echo "$DISTRIBUTION_RESULT" | jq -r '.Distribution.ARN')

echo -e "${GREEN}CloudFront distribution created: ${CLOUDFRONT_DISTRIBUTION_ID}${NC}"
echo -e "  Domain: ${CLOUDFRONT_DOMAIN_NAME}"

##############################################################################
# Step 4: Update S3 Bucket Policy for CloudFront Access
##############################################################################

echo ""
echo -e "${YELLOW}Step 4: Updating S3 bucket policy for CloudFront access...${NC}"

BUCKET_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "${CLOUDFRONT_ARN}"
                }
            }
        }
    ]
}
EOF
)

aws s3api put-bucket-policy \
    --bucket "${BUCKET_NAME}" \
    --policy "${BUCKET_POLICY}"

echo -e "${GREEN}Bucket policy updated${NC}"

##############################################################################
# Step 5: Configure CORS for API Access
##############################################################################

echo ""
echo -e "${YELLOW}Step 5: Configuring CORS for API access...${NC}"

CORS_CONFIG=$(cat <<EOF
{
    "CORSRules": [
        {
            "AllowedOrigins": [
                "https://startupwebapp-api.mosaicmeshai.com",
                "https://*.mosaicmeshai.com"
            ],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedHeaders": ["*"],
            "MaxAgeSeconds": 3600
        }
    ]
}
EOF
)

aws s3api put-bucket-cors \
    --bucket "${BUCKET_NAME}" \
    --cors-configuration "${CORS_CONFIG}"

echo -e "${GREEN}CORS configuration applied${NC}"

##############################################################################
# Step 6: Update aws-resources.env
##############################################################################

echo ""
echo -e "${YELLOW}Step 6: Updating aws-resources.env...${NC}"

# Update or add fields
update_env_var() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" "$ENV_FILE"; then
        sed -i.bak "s|^${key}=.*|${key}=\"${value}\"|" "$ENV_FILE"
    else
        echo "${key}=\"${value}\"" >> "$ENV_FILE"
    fi
}

update_env_var "S3_FRONTEND_BUCKET" "${BUCKET_NAME}"
update_env_var "CLOUDFRONT_DISTRIBUTION_ID" "${CLOUDFRONT_DISTRIBUTION_ID}"
update_env_var "CLOUDFRONT_DOMAIN_NAME" "${CLOUDFRONT_DOMAIN_NAME}"
update_env_var "CLOUDFRONT_ARN" "${CLOUDFRONT_ARN}"
update_env_var "CLOUDFRONT_OAC_ID" "${OAC_ID}"
update_env_var "FRONTEND_CUSTOM_DOMAIN" "${CUSTOM_DOMAIN}"

# Clean up backup file
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}aws-resources.env updated${NC}"

##############################################################################
# Step 7: Wait for Distribution Deployment
##############################################################################

echo ""
echo -e "${YELLOW}Step 7: Waiting for CloudFront distribution to deploy...${NC}"
echo -e "${YELLOW}This can take 5-15 minutes. You can Ctrl+C and check later.${NC}"
echo ""

# Poll for status
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    CF_STATUS=$(aws cloudfront get-distribution \
        --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --query 'Distribution.Status' \
        --output text)

    if [ "$CF_STATUS" = "Deployed" ]; then
        echo -e "${GREEN}CloudFront distribution is deployed!${NC}"
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo -e "  Status: ${CF_STATUS} (attempt ${ATTEMPT}/${MAX_ATTEMPTS})"
    sleep 15
done

if [ "$CF_STATUS" != "Deployed" ]; then
    echo -e "${YELLOW}Distribution still deploying. Check status later with:${NC}"
    echo -e "  aws cloudfront get-distribution --id ${CLOUDFRONT_DISTRIBUTION_ID} --query 'Distribution.Status'"
fi

##############################################################################
# Summary
##############################################################################

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Frontend Hosting Created Successfully${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}S3 Bucket:${NC}"
echo -e "  Name:               ${BUCKET_NAME}"
echo -e "  Public Access:      Blocked (CloudFront only)"
echo -e "  Versioning:         Enabled"
echo ""
echo -e "${GREEN}CloudFront Distribution:${NC}"
echo -e "  Distribution ID:    ${CLOUDFRONT_DISTRIBUTION_ID}"
echo -e "  Domain Name:        ${CLOUDFRONT_DOMAIN_NAME}"
echo -e "  Custom Domain:      ${CUSTOM_DOMAIN}"
echo -e "  Status:             ${CF_STATUS}"
echo -e "  HTTPS:              Enabled (TLS 1.2+)"
echo -e "  HTTP/2+3:           Enabled"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Configure DNS in Namecheap:"
echo -e "     CNAME: startupwebapp -> ${CLOUDFRONT_DOMAIN_NAME}"
echo -e ""
echo -e "  2. Upload frontend files to S3:"
echo -e "     aws s3 sync /path/to/frontend s3://${BUCKET_NAME} --delete"
echo -e ""
echo -e "  3. Update frontend index.js with production API URL:"
echo -e "     case 'startupwebapp.mosaicmeshai.com':"
echo -e "         api_url = 'https://startupwebapp-api.mosaicmeshai.com';"
echo -e "         break;"
echo ""
echo -e "${YELLOW}Access URLs (after DNS):${NC}"
echo -e "  Production:     https://${CUSTOM_DOMAIN}"
echo -e "  CloudFront:     https://${CLOUDFRONT_DOMAIN_NAME}"
echo ""
echo -e "${YELLOW}Upload Test:${NC}"
echo -e "  # Create a test file"
echo -e "  echo '<h1>Hello from StartupWebApp!</h1>' > /tmp/test.html"
echo -e "  aws s3 cp /tmp/test.html s3://${BUCKET_NAME}/test.html"
echo -e "  curl https://${CLOUDFRONT_DOMAIN_NAME}/test.html"
echo ""
echo -e "${GREEN}Phase 5.15 Progress:${NC}"
echo -e "  Step 1: Create Application Load Balancer (ALB)"
echo -e "  Step 2: Create ACM Certificate"
echo -e "  Step 3: Create HTTPS Listener"
echo -e "  Step 4: Configure Namecheap DNS"
echo -e "  Step 5: Create ECS Service Task Definition"
echo -e "  Step 6: Create ECS Service"
echo -e "  Step 6b: Configure Auto-Scaling"
echo -e "  ${GREEN}Step 7: Setup S3 + CloudFront${NC}"
echo -e "  -> Step 11: Final verification"
echo ""
