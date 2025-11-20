# ICE Asunción - Sistema Web

Sistema web para la Iglesia Cristiana Evangélica de Asunción.

## Características

- Gestión de contenido (noticias, boletines, mensajes)
- Sistema de miembros
- Panel administrativo personalizado
- Editor WYSIWYG para contenido
- Integración con Google Cloud Storage para archivos media
- Sistema de visitas y estadísticas
- Diseño responsivo y moderno

## Tecnologías

- Django 5.1.3
- PostgreSQL (Railway)
- Bootstrap 5.3.2
- Google Cloud Storage
- Whitenoise para archivos estáticos
- Gunicorn para producción

## Despliegue en Railway

### 1. Crear Proyecto en Railway

1. Crear cuenta en [Railway](https://railway.app)
2. Crear nuevo proyecto
3. Agregar PostgreSQL database
4. Conectar con el repositorio de GitHub

### 2. Variables de Entorno

Configurar las siguientes variables de entorno en Railway:

```bash
SECRET_KEY=tu-secret-key-segura
DEBUG=False
ALLOWED_HOSTS=.railway.app,tudominio.com
DATABASE_URL=(automático desde Railway PostgreSQL)
CSRF_TRUSTED_ORIGINS=https://tu-app.railway.app,https://tudominio.com

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-app
DEFAULT_FROM_EMAIL=noreply@tudominio.com

# Google Cloud Storage (opcional)
GS_BUCKET_NAME=tu-bucket
GS_PROJECT_ID=tu-proyecto-id
GS_CREDENTIALS_PATH=gcp-credentials.json
```

### 3. Desplegar

Railway detectará automáticamente el Procfile y desplegará la aplicación.

### 4. Migraciones y Superusuario

Después del primer despliegue, ejecutar en la consola de Railway:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Desarrollo Local

### 1. Clonar repositorio

```bash
git clone git@github.com:hernandezbg/ice_asuncion.git
cd ice_asuncion
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copiar `.env.example` a `.env` y configurar las variables necesarias.

### 5. Migraciones

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

## Estructura del Proyecto

```
ice_asuncion/
├── contenido/          # App para noticias, mensajes, páginas
├── miembros/           # App para gestión de miembros
├── panel/              # App para panel administrativo
├── ice_project/        # Configuración del proyecto
├── templates/          # Templates globales
├── static/             # Archivos estáticos
├── staticfiles/        # Archivos estáticos compilados
├── media/              # Archivos subidos (local)
├── requirements.txt    # Dependencias de Python
├── Procfile            # Configuración para Railway
└── runtime.txt         # Versión de Python
```

## Licencia

© 2025 ICE Asunción. Todos los derechos reservados.
