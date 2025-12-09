#!/bin/bash

##############################################################################
# Destroy S3 + CloudFront Frontend Hosting for StartupWebApp
#
# This script destroys:
# - CloudFront distribution (must be disabled first)
# - CloudFront Origin Access Control (OAC)
# - S3 bucket and all contents
#
# Order of operations (CloudFront requires specific sequence):
# 1. Disable CloudFront distribution
# 2. Wait for distribution to be deployed (disabled state)
# 3. Delete CloudFront distribution
# 4. Delete Origin Access Control
# 5. Empty and delete S3 bucket
#
# WARNING: This will DELETE all frontend files in S3!
#
# Usage: ./scripts/infra/destroy-frontend-hosting.sh
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
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"

echo -e "${BLUE}========================================${NC}"
echo -e "${RED}Destroy S3 + CloudFront Frontend Hosting${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Source existing resource IDs
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: aws-resources.env not found${NC}"
    exit 1
fi

source "$ENV_FILE"

# Check what resources exist
RESOURCES_FOUND=false

if [ -n "${CLOUDFRONT_DISTRIBUTION_ID:-}" ]; then
    CF_STATUS=$(aws cloudfront get-distribution \
        --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --query 'Distribution.Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    if [ "$CF_STATUS" != "NOT_FOUND" ]; then
        echo -e "${YELLOW}Found CloudFront distribution: ${CLOUDFRONT_DISTRIBUTION_ID} (${CF_STATUS})${NC}"
        RESOURCES_FOUND=true
    fi
fi

if [ -n "${S3_FRONTEND_BUCKET:-}" ]; then
    BUCKET_EXISTS=$(aws s3api head-bucket --bucket "${S3_FRONTEND_BUCKET}" 2>&1 || echo "NOT_FOUND")
    if [[ "$BUCKET_EXISTS" != *"NOT_FOUND"* ]] && [[ "$BUCKET_EXISTS" != *"404"* ]]; then
        # Count objects in bucket
        OBJECT_COUNT=$(aws s3 ls "s3://${S3_FRONTEND_BUCKET}" --recursive 2>/dev/null | wc -l || echo "0")
        echo -e "${YELLOW}Found S3 bucket: ${S3_FRONTEND_BUCKET} (${OBJECT_COUNT} objects)${NC}"
        RESOURCES_FOUND=true
    fi
fi

if [ -n "${CLOUDFRONT_OAC_ID:-}" ]; then
    OAC_EXISTS=$(aws cloudfront get-origin-access-control \
        --id "${CLOUDFRONT_OAC_ID}" 2>/dev/null || echo "NOT_FOUND")
    if [[ "$OAC_EXISTS" != *"NOT_FOUND"* ]]; then
        echo -e "${YELLOW}Found OAC: ${CLOUDFRONT_OAC_ID}${NC}"
        RESOURCES_FOUND=true
    fi
fi

if [ "$RESOURCES_FOUND" = false ]; then
    echo -e "${GREEN}No frontend hosting resources found to delete${NC}"
    exit 0
fi

echo ""
echo -e "${RED}WARNING: This will PERMANENTLY DELETE:${NC}"
echo -e "  - CloudFront distribution and all cache"
echo -e "  - S3 bucket and ALL frontend files"
echo -e "  - Origin Access Control"
echo ""
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to destroy frontend hosting? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

echo ""

##############################################################################
# Step 1: Disable CloudFront Distribution
##############################################################################

if [ -n "${CLOUDFRONT_DISTRIBUTION_ID:-}" ]; then
    CF_STATUS=$(aws cloudfront get-distribution \
        --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --query 'Distribution.Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")

    if [ "$CF_STATUS" != "NOT_FOUND" ]; then
        echo -e "${YELLOW}Step 1: Disabling CloudFront distribution...${NC}"

        # Get current distribution config and ETag
        DIST_CONFIG=$(aws cloudfront get-distribution-config \
            --id "${CLOUDFRONT_DISTRIBUTION_ID}")

        ETAG=$(echo "$DIST_CONFIG" | jq -r '.ETag')
        CONFIG=$(echo "$DIST_CONFIG" | jq '.DistributionConfig')

        # Check if already disabled
        IS_ENABLED=$(echo "$CONFIG" | jq -r '.Enabled')

        if [ "$IS_ENABLED" = "true" ]; then
            # Disable the distribution
            DISABLED_CONFIG=$(echo "$CONFIG" | jq '.Enabled = false')

            aws cloudfront update-distribution \
                --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
                --if-match "${ETAG}" \
                --distribution-config "${DISABLED_CONFIG}" > /dev/null

            echo -e "${GREEN}Distribution disabled, waiting for deployment...${NC}"

            # Wait for distribution to finish deploying
            echo -e "${YELLOW}This may take 5-15 minutes...${NC}"
            MAX_ATTEMPTS=60
            ATTEMPT=0
            while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
                CF_STATUS=$(aws cloudfront get-distribution \
                    --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
                    --query 'Distribution.Status' \
                    --output text)

                if [ "$CF_STATUS" = "Deployed" ]; then
                    echo -e "${GREEN}Distribution is deployed (disabled state)${NC}"
                    break
                fi

                ATTEMPT=$((ATTEMPT + 1))
                echo -e "  Status: ${CF_STATUS} (attempt ${ATTEMPT}/${MAX_ATTEMPTS})"
                sleep 15
            done
        else
            echo -e "${GREEN}Distribution already disabled${NC}"
        fi

        ##############################################################################
        # Step 2: Delete CloudFront Distribution
        ##############################################################################

        echo ""
        echo -e "${YELLOW}Step 2: Deleting CloudFront distribution...${NC}"

        # Get fresh ETag after disable
        ETAG=$(aws cloudfront get-distribution \
            --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
            --query 'ETag' \
            --output text)

        aws cloudfront delete-distribution \
            --id "${CLOUDFRONT_DISTRIBUTION_ID}" \
            --if-match "${ETAG}"

        echo -e "${GREEN}CloudFront distribution deleted${NC}"
    else
        echo -e "${YELLOW}CloudFront distribution not found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}No CloudFront distribution ID in env, skipping...${NC}"
fi

##############################################################################
# Step 3: Delete Origin Access Control
##############################################################################

echo ""
echo -e "${YELLOW}Step 3: Deleting Origin Access Control...${NC}"

if [ -n "${CLOUDFRONT_OAC_ID:-}" ]; then
    # Get ETag for OAC
    OAC_ETAG=$(aws cloudfront get-origin-access-control \
        --id "${CLOUDFRONT_OAC_ID}" \
        --query 'ETag' \
        --output text 2>/dev/null || echo "NOT_FOUND")

    if [ "$OAC_ETAG" != "NOT_FOUND" ]; then
        aws cloudfront delete-origin-access-control \
            --id "${CLOUDFRONT_OAC_ID}" \
            --if-match "${OAC_ETAG}"
        echo -e "${GREEN}OAC deleted: ${CLOUDFRONT_OAC_ID}${NC}"
    else
        echo -e "${YELLOW}OAC not found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}No OAC ID in env, skipping...${NC}"
fi

##############################################################################
# Step 4: Delete CloudFront Function
##############################################################################

echo ""
echo -e "${YELLOW}Step 4: Deleting CloudFront Function...${NC}"

FUNCTION_NAME="startupwebapp-directory-index"
FUNCTION_EXISTS=$(aws cloudfront describe-function \
    --name "${FUNCTION_NAME}" \
    --region us-east-1 2>/dev/null || echo "NOT_FOUND")

if [[ "$FUNCTION_EXISTS" != *"NOT_FOUND"* ]]; then
    FUNCTION_ETAG=$(echo "$FUNCTION_EXISTS" | jq -r '.ETag')
    aws cloudfront delete-function \
        --name "${FUNCTION_NAME}" \
        --if-match "${FUNCTION_ETAG}" \
        --region us-east-1
    echo -e "${GREEN}CloudFront Function deleted: ${FUNCTION_NAME}${NC}"
else
    echo -e "${YELLOW}CloudFront Function not found, skipping...${NC}"
fi

##############################################################################
# Step 5: Empty and Delete S3 Bucket
##############################################################################

echo ""
echo -e "${YELLOW}Step 5: Emptying and deleting S3 bucket...${NC}"

if [ -n "${S3_FRONTEND_BUCKET:-}" ]; then
    BUCKET_EXISTS=$(aws s3api head-bucket --bucket "${S3_FRONTEND_BUCKET}" 2>&1 || echo "NOT_FOUND")

    if [[ "$BUCKET_EXISTS" != *"NOT_FOUND"* ]] && [[ "$BUCKET_EXISTS" != *"404"* ]]; then
        # Delete all objects (including versions)
        echo -e "${YELLOW}Deleting all objects...${NC}"
        aws s3 rm "s3://${S3_FRONTEND_BUCKET}" --recursive 2>/dev/null || true

        # Delete all object versions (if versioning was enabled)
        echo -e "${YELLOW}Deleting object versions...${NC}"
        aws s3api list-object-versions \
            --bucket "${S3_FRONTEND_BUCKET}" \
            --query 'Versions[].{Key: Key, VersionId: VersionId}' \
            --output json 2>/dev/null | \
        jq -c '.[]' 2>/dev/null | while read -r obj; do
            KEY=$(echo "$obj" | jq -r '.Key')
            VERSION_ID=$(echo "$obj" | jq -r '.VersionId')
            if [ "$VERSION_ID" != "null" ]; then
                aws s3api delete-object \
                    --bucket "${S3_FRONTEND_BUCKET}" \
                    --key "$KEY" \
                    --version-id "$VERSION_ID" 2>/dev/null || true
            fi
        done

        # Delete delete markers
        echo -e "${YELLOW}Deleting delete markers...${NC}"
        aws s3api list-object-versions \
            --bucket "${S3_FRONTEND_BUCKET}" \
            --query 'DeleteMarkers[].{Key: Key, VersionId: VersionId}' \
            --output json 2>/dev/null | \
        jq -c '.[]' 2>/dev/null | while read -r obj; do
            KEY=$(echo "$obj" | jq -r '.Key')
            VERSION_ID=$(echo "$obj" | jq -r '.VersionId')
            if [ "$VERSION_ID" != "null" ]; then
                aws s3api delete-object \
                    --bucket "${S3_FRONTEND_BUCKET}" \
                    --key "$KEY" \
                    --version-id "$VERSION_ID" 2>/dev/null || true
            fi
        done

        # Delete the bucket
        echo -e "${YELLOW}Deleting bucket...${NC}"
        aws s3api delete-bucket --bucket "${S3_FRONTEND_BUCKET}"
        echo -e "${GREEN}S3 bucket deleted: ${S3_FRONTEND_BUCKET}${NC}"
    else
        echo -e "${YELLOW}S3 bucket not found, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}No S3 bucket name in env, skipping...${NC}"
fi

##############################################################################
# Step 6: Update aws-resources.env
##############################################################################

echo ""
echo -e "${YELLOW}Step 6: Updating aws-resources.env...${NC}"

# Clear frontend hosting fields
update_env_var() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" "$ENV_FILE"; then
        sed -i.bak "s|^${key}=.*|${key}=\"${value}\"|" "$ENV_FILE"
    fi
}

update_env_var "S3_FRONTEND_BUCKET" ""
update_env_var "CLOUDFRONT_DISTRIBUTION_ID" ""
update_env_var "CLOUDFRONT_DOMAIN_NAME" ""
update_env_var "CLOUDFRONT_ARN" ""
update_env_var "CLOUDFRONT_OAC_ID" ""
update_env_var "FRONTEND_CUSTOM_DOMAIN" ""

# Clean up backup file
rm -f "${ENV_FILE}.bak"

echo -e "${GREEN}aws-resources.env updated${NC}"

##############################################################################
# Summary
##############################################################################

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Frontend Hosting Destroyed Successfully${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Deleted:${NC}"
echo -e "  - CloudFront distribution"
echo -e "  - CloudFront Function (directory index)"
echo -e "  - Origin Access Control (OAC)"
echo -e "  - S3 bucket and all contents"
echo ""
echo -e "${YELLOW}Note:${NC}"
echo -e "  - DNS records in Namecheap should be removed manually"
echo -e "  - ACM certificate was NOT deleted (may be used by ALB)"
echo ""
echo -e "${YELLOW}To recreate:${NC}"
echo -e "  ./scripts/infra/create-frontend-hosting.sh"
echo ""
