#!/bin/bash
# Multi-Database Initialization Script for PostgreSQL
#
# This script creates multiple databases on a single PostgreSQL instance
# to support the multi-tenant architecture where different forked applications
# share the same RDS instance but have separate database namespaces.
#
# Usage: Set POSTGRES_MULTIPLE_DATABASES environment variable with comma-separated database names
# Example: POSTGRES_MULTIPLE_DATABASES=startupwebapp_dev,healthtech_dev,fintech_dev
#
# This script runs automatically when the PostgreSQL container is first initialized
# (via docker-entrypoint-initdb.d/)

set -e
set -u

# Function to create a single database
create_database() {
    local database=$1
    echo "Creating database: $database"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

# Main execution
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"

    # Parse comma-separated database names
    IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"

    # Create each database
    for db in "${DATABASES[@]}"; do
        # Trim whitespace
        db=$(echo "$db" | xargs)
        create_database "$db"
    done

    echo "Multiple databases created successfully"
else
    echo "POSTGRES_MULTIPLE_DATABASES not set, skipping multi-database creation"
fi
