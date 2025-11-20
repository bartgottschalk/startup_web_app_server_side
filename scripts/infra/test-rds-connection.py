#!/usr/bin/env python
"""
Test AWS RDS PostgreSQL Connection

This script tests the connection to AWS RDS using the production settings module.
It verifies that:
1. AWS Secrets Manager can be accessed
2. Database credentials are retrieved successfully
3. PostgreSQL connection can be established
4. Database schema is accessible

Usage:
    # Set environment variables
    export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
    export DATABASE_NAME=startupwebapp_prod
    export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
    export AWS_REGION=us-east-1

    # Run the test
    cd StartupWebApp
    python ../scripts/infra/test-rds-connection.py

IMPORTANT: Run this script in a separate terminal window, NOT in Claude chat
This is a one-time deployment validation tool, not part of the regular test suite.
"""
import os
import sys

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'StartupWebApp'))

import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StartupWebApp.settings_production')
django.setup()

from django.db import connection
from django.conf import settings


def test_secrets_manager():
    """Test that AWS Secrets Manager is accessible"""
    print("=" * 60)
    print("TEST 1: AWS Secrets Manager Access")
    print("=" * 60)

    try:
        import boto3
        from botocore.exceptions import ClientError

        secret_name = os.environ.get('DB_SECRET_NAME', 'rds/startupwebapp/multi-tenant/master')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        print(f"  Secret Name: {secret_name}")
        print(f"  AWS Region:  {aws_region}")

        client = boto3.client('secretsmanager', region_name=aws_region)
        response = client.get_secret_value(SecretId=secret_name)

        print("  ✅ SUCCESS: AWS Secrets Manager accessible")
        print(f"  ✅ Secret retrieved: {secret_name}")
        return True

    except ImportError:
        print("  ❌ FAILED: boto3 not installed")
        print("     Run: pip install boto3")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"  ❌ FAILED: Secret '{secret_name}' not found in region {aws_region}")
        elif error_code == 'AccessDeniedException':
            print(f"  ❌ FAILED: Access denied to secret '{secret_name}'")
            print("     Check IAM permissions for AWS credentials")
        else:
            print(f"  ❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_database_configuration():
    """Test that database settings are correctly configured"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Configuration")
    print("=" * 60)

    try:
        db_config = settings.DATABASES['default']

        print(f"  Engine:   {db_config['ENGINE']}")
        print(f"  Database: {db_config['NAME']}")
        print(f"  Host:     {db_config['HOST']}")
        print(f"  Port:     {db_config['PORT']}")
        print(f"  User:     {db_config['USER']}")
        print(f"  SSL Mode: {db_config['OPTIONS'].get('sslmode', 'Not configured')}")

        # Check for required fields
        required_fields = ['ENGINE', 'NAME', 'HOST', 'PORT', 'USER', 'PASSWORD']
        for field in required_fields:
            if not db_config.get(field):
                print(f"  ❌ FAILED: Missing required field: {field}")
                return False

        print("  ✅ SUCCESS: Database configuration valid")
        return True

    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_database_connection():
    """Test that PostgreSQL connection can be established"""
    print("\n" + "=" * 60)
    print("TEST 3: Database Connection")
    print("=" * 60)

    try:
        # Attempt to connect
        connection.ensure_connection()

        print(f"  ✅ SUCCESS: Connected to database")
        print(f"  Database: {connection.settings_dict['NAME']}")
        print(f"  Host:     {connection.settings_dict['HOST']}")

        return True

    except Exception as e:
        print(f"  ❌ FAILED: Could not connect to database")
        print(f"     Error: {e}")
        return False


def test_database_query():
    """Test that database queries work"""
    print("\n" + "=" * 60)
    print("TEST 4: Database Query")
    print("=" * 60)

    try:
        with connection.cursor() as cursor:
            # Get PostgreSQL version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"  PostgreSQL Version: {version[0][:50]}...")

            # Get current database
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"  Current Database: {db_name[0]}")

            # Count tables in public schema
            cursor.execute(
                "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';"
            )
            table_count = cursor.fetchone()
            print(f"  Tables in public schema: {table_count[0]}")

            print("  ✅ SUCCESS: Database queries working")
            return True

    except Exception as e:
        print(f"  ❌ FAILED: Database query failed")
        print(f"     Error: {e}")
        return False


def test_django_apps():
    """Test that Django apps are properly configured"""
    print("\n" + "=" * 60)
    print("TEST 5: Django Configuration")
    print("=" * 60)

    try:
        from django.apps import apps

        installed_apps = apps.get_app_configs()
        app_names = [app.name for app in installed_apps]

        print(f"  Installed Apps: {len(app_names)}")

        # Check for our custom apps
        required_apps = ['order', 'user', 'clientevent']
        for app in required_apps:
            if app in app_names:
                print(f"    ✅ {app}")
            else:
                print(f"    ❌ {app} (missing)")
                return False

        print(f"  DEBUG: {settings.DEBUG}")
        print(f"  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

        print("  ✅ SUCCESS: Django configuration valid")
        return True

    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def main():
    """Run all connection tests"""
    print("\n" + "=" * 60)
    print("AWS RDS PostgreSQL Connection Test")
    print("=" * 60)
    print(f"Settings Module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Database Name:   {os.environ.get('DATABASE_NAME', 'default')}")
    print()

    tests = [
        test_secrets_manager,
        test_database_configuration,
        test_database_connection,
        test_database_query,
        test_django_apps,
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"  Passed: {passed}/{total}")

    if all(results):
        print("\n  ✅ ALL TESTS PASSED - RDS Connection Ready!")
        print("\n  Next steps:")
        print("    1. Run migrations: python manage.py migrate")
        print("    2. Create superuser: python manage.py createsuperuser")
        print("    3. Run test suite: python manage.py test")
        return 0
    else:
        print("\n  ❌ SOME TESTS FAILED - Review errors above")
        print("\n  Common issues:")
        print("    1. Check AWS credentials are configured (aws configure)")
        print("    2. Check IAM permissions for Secrets Manager")
        print("    3. Check RDS security group allows your IP")
        print("    4. Check DATABASE_NAME environment variable is set")
        return 1


if __name__ == '__main__':
    sys.exit(main())
