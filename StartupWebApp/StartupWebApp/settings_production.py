"""
Production settings for AWS deployment with RDS PostgreSQL

This module extends the base settings for production deployment on AWS.
It retrieves ALL secrets from AWS Secrets Manager including database credentials,
Django SECRET_KEY, Stripe keys, and email credentials.

Usage:
    export DJANGO_SETTINGS_MODULE=StartupWebApp.settings_production
    export DATABASE_NAME=startupwebapp_prod  # or healthtech_experiment, fintech_experiment
    export DB_SECRET_NAME=rds/startupwebapp/multi-tenant/master
    export AWS_REGION=us-east-1
    export ALLOWED_HOSTS=www.mosaicmeshai.com
    python manage.py migrate
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

# AWS Region
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def get_secret(secret_name):
    """
    Retrieve secret from AWS Secrets Manager

    Args:
        secret_name (str): Name or ARN of the secret

    Returns:
        dict: Secret data as dictionary

    Raises:
        Exception: If secret retrieval fails
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("boto3 not installed. Run: pip install boto3")
        raise

    client = boto3.client('secretsmanager', region_name=AWS_REGION)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            logger.error(f"Secret {secret_name} not found in region {AWS_REGION}")
        elif error_code == 'AccessDeniedException':
            logger.error(f"Access denied to secret {secret_name}. Check IAM permissions.")
        else:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise


# Retrieve ALL secrets from Secrets Manager
secret_name = os.environ.get('DB_SECRET_NAME', 'rds/startupwebapp/multi-tenant/master')
try:
    secrets = get_secret(secret_name)
    logger.info(f"Successfully retrieved secrets from {secret_name}")
except Exception as e:
    logger.error(f"Failed to retrieve secrets: {e}")
    # For initial setup/testing, allow fallback to environment variables
    secrets = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '5432')),
        'username': os.environ.get('DB_USER', 'django_app'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'django_secret_key': os.environ.get('DJANGO_SECRET_KEY', 'insecure-fallback-key-change-me'),
        'stripe_secret_key': os.environ.get('STRIPE_SECRET_KEY', ''),
        'stripe_publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY', ''),
        'email_host': os.environ.get('EMAIL_HOST', ''),
        'email_port': int(os.environ.get('EMAIL_PORT', '587')),
        'email_user': os.environ.get('EMAIL_USER', ''),
        'email_password': os.environ.get('EMAIL_PASSWORD', ''),
    }
    logger.warning("Using fallback credentials from environment variables")

# Import base settings AFTER retrieving secrets
# This allows us to override SECRET_KEY before settings.py tries to use it
from .settings import *  # noqa: F403,F401,E402

# Override DEBUG for production
DEBUG = False

# Django SECRET_KEY from Secrets Manager
SECRET_KEY = secrets.get('django_secret_key', 'INSECURE-CHANGE-ME')  # noqa: F405

# Allowed hosts from environment
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',')]  # noqa: F405
else:
    # Default for StartupWebApp production
    # Include API subdomain and localhost for ALB health checks
    # ALB health checker uses private IP as Host header, so we allow internal VPC ranges
    ALLOWED_HOSTS = [  # noqa: F405
        'www.mosaicmeshai.com',
        'startupwebapp-api.mosaicmeshai.com',
        'localhost',
        '127.0.0.1',
    ]

# Fetch container's own IP from ECS metadata for ALB health checks
# ALB sends health check requests with the task's private IP as the Host header
# VPC CIDR: 10.0.0.0/16, Private subnets: 10.0.10.0/24 and 10.0.11.0/24


def get_ecs_container_ip():
    """Fetch container IP from ECS metadata endpoint (Fargate only)"""
    import urllib.request
    metadata_uri = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')
    if not metadata_uri:
        return None
    try:
        with urllib.request.urlopen(f"{metadata_uri}/task", timeout=2) as response:
            data = json.loads(response.read().decode())
            # Navigate to: Containers[0].Networks[0].IPv4Addresses[0]
            containers = data.get('Containers', [])
            if containers:
                networks = containers[0].get('Networks', [])
                if networks:
                    ipv4_addresses = networks[0].get('IPv4Addresses', [])
                    if ipv4_addresses:
                        return ipv4_addresses[0]
    except Exception as e:
        logger.warning(f"Could not fetch ECS container IP: {e}")
    return None


container_ip = get_ecs_container_ip()
if container_ip:
    ALLOWED_HOSTS.append(container_ip)
    logger.info(f"Added container IP to ALLOWED_HOSTS: {container_ip}")

# Database configuration for AWS RDS PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'startupwebapp_prod'),  # Fork-specific
        'USER': secrets.get('username', 'django_app'),
        'PASSWORD': secrets.get('password', ''),
        'HOST': secrets.get('host', 'localhost'),
        'PORT': secrets.get('port', 5432),
        'CONN_MAX_AGE': 600,  # Connection pooling (10 minutes)
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL for security
            'connect_timeout': 10,  # Connection timeout in seconds
        },
    }
}

# Stripe configuration from Secrets Manager
STRIPE_SERVER_SECRET_KEY = secrets.get('stripe_secret_key', '')
STRIPE_PUBLISHABLE_SECRET_KEY = secrets.get('stripe_publishable_key', '')
STRIPE_LOG_LEVEL = 'info'  # Production: less verbose than 'debug'

# Email configuration from Secrets Manager
EMAIL_HOST = secrets.get('email_host', '')
EMAIL_PORT = secrets.get('email_port', 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = secrets.get('email_user', '')
EMAIL_HOST_PASSWORD = secrets.get('email_password', '')

# Production Security Settings (enforced when DEBUG=False)
SECURE_SSL_REDIRECT = True
# Tell Django to trust X-Forwarded-Proto header from ALB (which terminates SSL)
# Without this, Django sees HTTP requests and tries to redirect to HTTPS, causing a loop
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Exempt health check path from SSL redirect - ALB health checks hit port 8000 directly
# over HTTP and don't include X-Forwarded-Proto header
SECURE_REDIRECT_EXEMPT = [r'^order/products/$']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session and CSRF cookies for production
# Use domain prefix dot to allow sharing across subdomains (www, api)
SESSION_COOKIE_DOMAIN = ".mosaicmeshai.com"
CSRF_COOKIE_DOMAIN = ".mosaicmeshai.com"  # Share CSRF cookies across subdomains

# CSRF Configuration for production
CSRF_TRUSTED_ORIGINS = [
    'https://www.mosaicmeshai.com',
    'https://mosaicmeshai.com',
    'https://startupwebapp-api.mosaicmeshai.com',
]

# CORS Configuration for production
CORS_ORIGIN_WHITELIST = (
    'https://www.mosaicmeshai.com',
    'https://mosaicmeshai.com',
    'https://startupwebapp-api.mosaicmeshai.com',
)

# Logging configuration for production (CloudWatch compatible)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Only log slow queries and errors
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',  # Log 4xx/5xx errors
            'propagate': False,
        },
        'order': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'user': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'clientevent': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Static and Media files
# TODO: Configure S3 bucket for static/media files in future deployment
# For now, use local static files (served by nginx or whitenoise)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # noqa: F405

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # noqa: F405

# Configuration summary (logging happens at application startup, not module import)
# Database: DATABASES['default']['NAME']
# Host: DATABASES['default']['HOST']
# Allowed hosts: ALLOWED_HOSTS
# Email configured: bool(EMAIL_HOST)
# Stripe configured: bool(STRIPE_SERVER_SECRET_KEY)
