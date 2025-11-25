# Guía de Despliegue en Railway

## ✅ Archivos Preparados

El proyecto ya tiene todos los archivos necesarios para Railway:

- ✅ `Procfile` - Configuración de Gunicorn
- ✅ `runtime.txt` - Versión de Python 3.12
- ✅ `requirements.txt` - Dependencias del proyecto
- ✅ `.gitignore` - Archivos excluidos
- ✅ `README.md` - Documentación
- ✅ `.env.example` - Ejemplo de variables de entorno
- ✅ Código subido a GitHub en la rama `master`

## 📋 Pasos para Desplegar en Railway

### 1. Crear Proyecto en Railway

1. Ir a [railway.app](https://railway.app)
2. Iniciar sesión con GitHub
3. Clic en "New Project"
4. Seleccionar "Deploy from GitHub repo"
5. Autorizar Railway a acceder a tus repositorios
6. Seleccionar el repositorio `hernandezbg/ice_asuncion`
7. Seleccionar la rama `master`

### 2. Agregar PostgreSQL Database

1. En el dashboard del proyecto, clic en "+ New"
2. Seleccionar "Database"
3. Seleccionar "Add PostgreSQL"
4. Railway creará automáticamente la base de datos y la variable `DATABASE_URL`

### 3. Configurar Variables de Entorno

En el servicio de la aplicación (no en la base de datos), ir a "Variables" y agregar:

#### Variables Obligatorias:

```bash
SECRET_KEY=genera-una-clave-secreta-aleatoria-aqui
DEBUG=False
ALLOWED_HOSTS=.railway.app,iceasuncion.org,www.iceasuncion.org
CSRF_TRUSTED_ORIGINS=https://tu-app.railway.app,https://iceasuncion.org,https://www.iceasuncion.org
```

**IMPORTANTE**: Para generar un SECRET_KEY seguro, usa:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Variables Opcionales (Email):

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-app
DEFAULT_FROM_EMAIL=noreply@iceasuncion.org
```

**Nota**: Para Gmail, necesitas crear una "Contraseña de aplicación" en tu cuenta de Google.

#### Variables Opcionales (Google Cloud Storage):

Si quieres usar GCS para archivos media:

```bash
GS_BUCKET_NAME=nombre-del-bucket
GS_PROJECT_ID=id-del-proyecto
GS_CREDENTIALS_PATH=gcp-credentials.json
```

### 4. Despliegue Inicial

Railway detectará automáticamente que es un proyecto Django y comenzará el despliegue.

Esperá a que termine el build (puede tardar 2-3 minutos).

### 5. Ejecutar Migraciones

Una vez desplegado, abrí la consola de Railway:

1. En el dashboard del proyecto, clic en tu servicio
2. Ir a la pestaña "Settings"
3. En la sección "Service", buscar "Deploy Logs"
4. O ir a la pestaña "Deployments" y clic en el deployment activo
5. Clic en "View Logs"
6. Luego ir a la pestaña "Settings" > "Deploy" > "Custom Start Command" o usar la consola

Para abrir la consola:
- Desde la UI: Ir al servicio > "..." (menú) > "Service Console"

Ejecutar los siguientes comandos:

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic --noinput
```

### 6. Verificar el Despliegue

1. Railway te asignará un dominio automático: `tu-app.railway.app`
2. Ir a ese dominio y verificar que el sitio carga correctamente
3. Probar el login en `/panel/login/` con el superusuario creado

### 7. Configurar Dominio Personalizado (Opcional)

Si tenés un dominio propio:

1. En Railway, ir a tu servicio
2. Ir a "Settings" > "Domains"
3. Clic en "Add Domain"
4. Ingresar tu dominio (ej: `iceasuncion.org`)
5. Railway te dará un registro CNAME o A para configurar en tu DNS
6. Agregar ese registro en tu proveedor de DNS
7. Actualizar `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con tu dominio

### 8. Monitoreo y Logs

- **Ver logs en tiempo real**: Railway Dashboard > Tu servicio > "Logs"
- **Métricas**: Railway Dashboard > Tu servicio > "Metrics"
- **Reiniciar servicio**: Settings > "Redeploy"

## 🔧 Troubleshooting

### Error: "Invalid HTTP_HOST header"

Agregá tu dominio de Railway a las variables de entorno:
```bash
ALLOWED_HOSTS=.railway.app,tu-dominio.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-dominio.railway.app
```

### Error: "Static files not loading"

Ejecutar:
```bash
python manage.py collectstatic --noinput
```

### Error de base de datos

Verificá que:
1. El servicio de PostgreSQL esté corriendo
2. La variable `DATABASE_URL` esté configurada automáticamente
3. Las migraciones se hayan aplicado correctamente

### Error 500 en producción

1. Revisar los logs en Railway
2. Verificar que `DEBUG=False` esté configurado
3. Verificar que `SECRET_KEY` esté configurada
4. Verificar que las migraciones se ejecutaron

## 📊 Comandos Útiles en Railway Console

```bash
# Ver migraciones pendientes
python manage.py showmigrations

# Crear backup de la base de datos (desde Railway PostgreSQL)
pg_dump $DATABASE_URL > backup.sql

# Ver versión de Python
python --version

# Ver dependencias instaladas
pip list

# Acceder a shell de Django
python manage.py shell

# Crear datos de prueba (si lo necesitas)
python manage.py loaddata nombre_fixture.json
```

## 🔒 Seguridad en Producción

El proyecto ya está configurado para producción cuando `DEBUG=False`:

- ✅ SSL redirect habilitado
- ✅ Secure cookies
- ✅ CSRF protection
- ✅ XSS filtering
- ✅ Content type sniffing protection
- ✅ X-Frame-Options configurado

## 🚀 Actualizaciones Futuras

Para desplegar actualizaciones:

1. Hacer cambios en local
2. Commit y push a GitHub:
   ```bash
   git add .
   git commit -m "Descripción de cambios"
   git push origin master
   ```
3. Railway detectará el push y redesplegará automáticamente
4. Si hay cambios en modelos, ejecutar migraciones desde la consola:
   ```bash
   python manage.py migrate
   ```

## 📞 Soporte

Si tenés problemas:

1. Revisar los logs en Railway Dashboard
2. Verificar la documentación de Railway: https://docs.railway.app
3. Revisar el README.md del proyecto

---

**Repositorio**: https://github.com/hernandezbg/ice_asuncion
**Tecnologías**: Django 5.1.3, PostgreSQL, Railway, Whitenoise, Bootstrap 5
