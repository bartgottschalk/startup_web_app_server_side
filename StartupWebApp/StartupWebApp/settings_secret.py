# Secret settings for local unit testing
# Based on buildspec_unit_tests.yml

SECRET_KEY = 'uM*&23jb29872(*&$GSKkQPy)(!&^%#0X8aG3ZQp&^%@#lkXrCTqmOS0gMnX'

ALLOWED_HOSTS = ['localapi.startupwebapp.com', 'localliveservertestcaseapi.startupwebapp.com']

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_DOMAIN = "localapi.startupwebapp.com"

CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = "localhost.startupwebapp.com"

DEBUG = True

ENVIRONMENT_DOMAIN = 'http://localhost.startupwebapp.com'

EMAIL_HOST_USER = 'AKIAJOVIUIENKNYU56ZA'
EMAIL_HOST_PASSWORD = 'BBlkKh47UslsZxbarkx666TSC7wkpYMLCZXdsxwxsck4'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'rg_unittest',
        'USER': 'django_unittest',
        'PASSWORD': 'imatester',
        'HOST': '127.0.0.1',
    }
}

S3_QR_IMAGE_BUCKET_PATH = 'food/qr/local/'
S3_ORDER_PDF_BUCKET_PATH = 'pdf/local/'
S3_FOOD_IMAGE_BUCKET_PATH = 'food/main/local/'

STRIPE_SERVER_SECRET_KEY = 'sk_test_O9l7Y5jpB3OpYQrtinEwjYhB'
STRIPE_PUBLISHABLE_SECRET_KEY = 'pk_test_9dMmGoPijqBpKLrIX4hq8XAG'
STRIPE_LOG_LEVEL = 'debug'

# CORS Config
CORS_ORIGIN_WHITELIST = (
    'http://localliveservertestcase.startupwebapp.com',
    'http://localhost.startupwebapp.com',
)
