#!/bin/bash

##############################################################################
# Common initialization for infrastructure scripts
#
# This script initializes the aws-resources.env file from template
# and sets up common variables
#
# Usage: Source this script at the beginning of each infrastructure script:
#   source "${SCRIPT_DIR}/init-env.sh"
##############################################################################

# Get script directory (should be set by calling script)
if [ -z "$SCRIPT_DIR" ]; then
    echo "Error: SCRIPT_DIR must be set before sourcing init-env.sh"
    exit 1
fi

# File paths
ENV_FILE="${SCRIPT_DIR}/aws-resources.env"
ENV_TEMPLATE="${SCRIPT_DIR}/aws-resources.env.template"

# Initialize env file from template if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$ENV_TEMPLATE" ]; then
        echo -e "${RED}Error: Template file not found: ${ENV_TEMPLATE}${NC}"
        echo -e "${RED}This is a required file that should be committed to git.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Initializing aws-resources.env from template...${NC}"
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    echo -e "${GREEN}✓ aws-resources.env created (will be populated during deployment)${NC}"
    echo ""
fi
