"""
Django settings for ice_project.
"""

from pathlib import Path
from decouple import config, Csv
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'django_summernote',
    'storages',

    # My apps
    'contenido',
    'miembros',
    'panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Whitenoise después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'panel.middleware.VisitasMiddleware',  # Rastreo de visitas
]

ROOT_URLCONF = 'ice_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Templates globales
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # Para acceder a MEDIA_URL en templates
                'contenido.context_processors.datos_ice',  # Datos de ICE disponibles en todos los templates
                'contenido.context_processors.paginas_menu',  # Páginas para el menú de navegación
            ],
        },
    },
]

WSGI_APPLICATION = 'ice_project.wsgi.application'

# Database - Railway PostgreSQL
# Uso directamente la URL de conexión de Railway
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    ),
    # Base de datos antigua para migración
    'old_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iceasuncionnew',
        'USER': 'iceasuncion',
        'PASSWORD': 'Despojado82',
        'HOST': 'vps-1873275-x.dattaweb.com',
        'PORT': '5246',
        'OPTIONS': {
            'sslmode': 'disable',
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Servidos con Whitenoise
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Google Cloud Storage para archivos MEDIA (opcional)
GS_BUCKET_NAME = config('GS_BUCKET_NAME', default='')
GS_PROJECT_ID = config('GS_PROJECT_ID', default='')
# Credenciales pueden venir de archivo o de variable de entorno (JSON en base64)
GS_CREDENTIALS_PATH = config('GS_CREDENTIALS_PATH', default='')
GS_CREDENTIALS_JSON = config('GS_CREDENTIALS_JSON', default='')

# Configuración de almacenamiento
# Por defecto usa FileSystemStorage, solo usa GCS si está configurado
USE_GCS = False

if GS_BUCKET_NAME and GS_PROJECT_ID:
    # Opción 1: Credenciales desde variable de entorno (JSON en base64) - para Railway
    if GS_CREDENTIALS_JSON:
        import base64

        try:
            credentials_json = base64.b64decode(GS_CREDENTIALS_JSON).decode('utf-8')
            credentials_file = BASE_DIR / 'gcp-credentials-temp.json'
            with open(credentials_file, 'w') as f:
                f.write(credentials_json)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_file)
            if credentials_file.exists():
                USE_GCS = True
        except Exception as e:
            print(f"Error al cargar credenciales GCS: {e}")
            USE_GCS = False

    # Opción 2: Credenciales desde archivo local - para desarrollo
    elif GS_CREDENTIALS_PATH:
        credentials_file = BASE_DIR / GS_CREDENTIALS_PATH
        if credentials_file.exists():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_file)
            USE_GCS = True

if USE_GCS:
    GS_DEFAULT_ACL = None
    GS_FILE_OVERWRITE = False
    GS_LOCATION = 'media'  # Prefijo en el bucket: ice-asuncion-media/media/
    GS_QUERYSTRING_AUTH = True
    GS_EXPIRATION = 3600

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    print("=== GCS CONFIGURADO ===")
    print(f"Bucket: {GS_BUCKET_NAME}")
    print(f"Location: {GS_LOCATION}")
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    print("=== USANDO FILESYSTEM LOCAL ===")


# Crispy Forms - Bootstrap 5
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Summernote Configuration
SUMMERNOTE_CONFIG = {
    'summernote': {
        'width': '100%',
        'height': '400',
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['fontname', ['fontname']],
            ['fontsize', ['fontsize']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['height', ['height']],
            ['table', ['table']],
            ['insert', ['link', 'picture', 'video']],
            ['view', ['fullscreen', 'codeview']],
        ],
    },
    'iframe': True,
    'lazy': True,
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@iceasuncion.org')

# Login URLs
LOGIN_URL = 'panel:login'
LOGIN_REDIRECT_URL = 'panel:dashboard'
LOGOUT_REDIRECT_URL = 'panel:login'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
