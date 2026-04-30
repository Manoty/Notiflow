import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv('SECRET_KEY')
DEBUG        = os.getenv('DEBUG', 'False') == 'True'
ENVIRONMENT  = os.getenv('ENVIRONMENT', 'development')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Check your .env file.")

# ── Apps ──────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'background_task',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'notifications.middleware.RequestLoggingMiddleware',  # Phase 11
]

ROOT_URLCONF    = 'notiflow_backend.urls'
WSGI_APPLICATION = 'notiflow_backend.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':       'django.db.backends.postgresql',
        'NAME':         os.getenv('DB_NAME'),
        'USER':         os.getenv('DB_USER'),
        'PASSWORD':     os.getenv('DB_PASSWORD'),
        'HOST':         os.getenv('DB_HOST', 'localhost'),
        'PORT':         os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', 60)),
        'OPTIONS': {
            'connect_timeout': 5,
        },
    }
}

# ── Templates ─────────────────────────────────────────────────────────────
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ── Email ─────────────────────────────────────────────────────────────────
EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT         = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Notiflow <noreply@notiflow.dev>')

# ── SMS ───────────────────────────────────────────────────────────────────
SMS_PROVIDER  = os.getenv('SMS_PROVIDER', 'simulated')
SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'NOTIFLOW')
AT_USERNAME   = os.getenv('AT_USERNAME', '')
AT_API_KEY    = os.getenv('AT_API_KEY', '')

# ── API Keys ──────────────────────────────────────────────────────────────
# Parsed from: "tixora:key1,scott:key2"
def _parse_api_keys(raw: str) -> dict:
    keys = {}
    if not raw:
        return keys
    for pair in raw.split(','):
        pair = pair.strip()
        if ':' in pair:
            app_id, key = pair.split(':', 1)
            keys[key.strip()] = app_id.strip()
    return keys

NOTIFLOW_API_KEYS = _parse_api_keys(os.getenv('NOTIFLOW_API_KEYS', ''))

# ── Rate limiting ─────────────────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))

# ── CORS ──────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# ── DRF ───────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES':   ['rest_framework.parsers.JSONParser'],
    'EXCEPTION_HANDLER':        'notifications.exceptions.notiflow_exception_handler',
}

# ── Background tasks ─────────────────────────────────────────────────────
MAX_ATTEMPTS              = 3
MAX_RUN_TIME              = 60
BACKGROUND_TASK_RUN_ASYNC = False

# ── Logging ───────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE  = os.getenv('LOG_FILE', 'logs/notiflow.log')

# Ensure log directory exists
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'notifications.logging_utils.JSONFormatter',
        },
        'console': {
            'format': '[{asctime}] {levelname:8} {name}: {message}',
            'style':  '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'console',
        },
        'file': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    LOG_FILE,
            'maxBytes':    10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter':   'json',
            'encoding':    'utf-8',
        },
    },
    'loggers': {
        'notifications': {
            'handlers':  ['console', 'file'],
            'level':     LOG_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['file'],
            'level':     'WARNING',
            'propagate': False,
        },
    },
}

# ── Static files ──────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security headers (production only) ────────────────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER    = True
    SECURE_CONTENT_TYPE_NOSNIFF  = True
    X_FRAME_OPTIONS              = 'DENY'