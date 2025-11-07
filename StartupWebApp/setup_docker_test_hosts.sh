#!/bin/bash
# Setup /etc/hosts for Docker functional tests to enable cookie sharing
#
# WHY THIS IS NEEDED:
# - Functional tests use Selenium to test the full stack
# - Frontend served at: localliveservertestcase.startupwebapp.com
# - Backend API at: localliveservertestcaseapi.startupwebapp.com:60767
# - Both share parent domain ".startupwebapp.com" to enable CSRF cookie sharing
# - Without this setup, AJAX POST requests fail with 403 Forbidden (missing CSRF token)
#
# WHEN TO RUN:
# - Before first functional test run
# - After each container restart/rebuild
#
# USAGE:
#   docker-compose exec backend bash /app/setup_docker_test_hosts.sh

# Get the IP address of the frontend container from the Docker network
FRONTEND_IP=$(getent hosts frontend | awk '{ print $1 }')

echo "Setting up /etc/hosts for functional tests..."
echo "Frontend container IP: $FRONTEND_IP"

# Add entries to /etc/hosts
echo "$FRONTEND_IP    localliveservertestcase.startupwebapp.com" >> /etc/hosts
echo "127.0.0.1        localliveservertestcaseapi.startupwebapp.com" >> /etc/hosts

echo "/etc/hosts updated successfully"
cat /etc/hosts | grep startupwebapp.com
