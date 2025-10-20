# 🚀 Guía de Deployment en Railway

Esta guía te ayudará a desplegar RemiBOT en Railway paso a paso.

## 📋 Pre-requisitos

1. **Cuenta en Railway**: [railway.app](https://railway.app)
2. **Cuenta en Supabase**: [supabase.com](https://supabase.com)
3. **Repositorio Git**: Tu código debe estar en GitHub/GitLab/Bitbucket
4. **API Keys**: OpenAI o Anthropic (Claude)
5. **WhatsApp Business API**: Token y Phone ID (opcional para testing inicial)

---

## 🎯 Estrategia de Deployment

Vamos a crear **2 servicios** en Railway:
1. **Backend** (FastAPI - Python)
2. **Frontend** (React + Vite - Node.js)

---

## 📦 Paso 1: Preparar Supabase

### 1.1 Crear proyecto en Supabase
1. Ve a [supabase.com](https://supabase.com)
2. Crea un nuevo proyecto
3. Espera a que se inicialice (2-3 minutos)

### 1.2 Ejecutar migraciones
1. Ve a **SQL Editor** en el dashboard de Supabase
2. Ejecuta las migraciones en orden:
   - `infra/supabase/migrations/0001_init.sql`
   - `infra/supabase/migrations/0002_telefonos_empresa.sql`

### 1.3 Obtener credenciales
Ve a **Settings > API** y copia:
- `SUPABASE_URL`: Project URL
- `SUPABASE_ANON_KEY`: anon/public key
- `SUPABASE_SERVICE_ROLE_KEY`: service_role key (⚠️ mantener secreto)

---

## 🚂 Paso 2: Desplegar Backend en Railway

### 2.1 Crear nuevo proyecto
1. En tu dashboard de Railway, haz clic en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Autoriza Railway a acceder a tu repositorio
4. Selecciona el repositorio **RemiBOT**

### 2.2 Configurar el servicio Backend
1. Railway detectará automáticamente que es un proyecto Python
2. Configura el **Root Directory**: `/backend`
3. Railway usará el archivo `backend/railway.json` automáticamente

### 2.3 Agregar variables de entorno
En **Variables** del servicio backend, agrega:

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# LLM (al menos una)
OPENAI_API_KEY=sk-proj-xxx
CLAUDE_API_KEY=sk-ant-xxx

# WhatsApp (opcional - puedes agregarlo después)
WHATSAPP_TOKEN=EAAxxxxx
WHATSAPP_PHONE_ID=123456789
WHATSAPP_API_VERSION=v18.0

# General
ENVIRONMENT=production
FRONTEND_URL=https://tu-frontend.railway.app
```

### 2.4 Deploy
1. Haz clic en **"Deploy"**
2. Espera a que termine el build (2-3 minutos)
3. Railway te dará una URL pública: `https://xxx.railway.app`
4. **Guarda esta URL** - la necesitarás para el frontend

---

## 🎨 Paso 3: Desplegar Frontend en Railway

### 3.1 Agregar nuevo servicio
1. En el mismo proyecto de Railway, haz clic en **"New Service"**
2. Selecciona **"GitHub Repo"** (el mismo repositorio)
3. Configura el **Root Directory**: `/frontend`

### 3.2 Configurar variables de entorno
En **Variables** del servicio frontend, agrega:

```bash
VITE_BACKEND_BASE_URL=https://tu-backend.railway.app
```

⚠️ **IMPORTANTE**: Reemplaza `tu-backend.railway.app` con la URL real del backend del Paso 2.4

### 3.3 Deploy
1. Haz clic en **"Deploy"**
2. Espera a que termine el build (3-4 minutos)
3. Railway te dará una URL pública: `https://yyy.railway.app`

---

## ✅ Paso 4: Verificar el Deployment

### 4.1 Verificar Backend
Abre en tu navegador:
```
https://tu-backend.railway.app/docs
```

Deberías ver la documentación interactiva de FastAPI (Swagger UI).

### 4.2 Verificar Frontend
Abre en tu navegador:
```
https://tu-frontend.railway.app
```

Deberías ver el panel administrativo de RemiBOT.

### 4.3 Probar la conexión
1. Ve a la sección **"Configuración"** en el frontend
2. Verifica que puedas ver/editar la configuración
3. Si hay errores de CORS, verifica que `FRONTEND_URL` en el backend esté correctamente configurado

---

## 🔧 Paso 5: Configuración Inicial

### 5.1 Crear empresa de prueba
Ejecuta este SQL en Supabase SQL Editor:

```sql
-- Crear empresa de prueba
INSERT INTO empresas (nombre, activo) 
VALUES ('Mi Empresa Test', true)
RETURNING id;

-- Anota el ID que te devuelve (ejemplo: 1)

-- Crear establecimiento
INSERT INTO establecimientos (empresa_id, nombre, activo)
VALUES (1, 'Establecimiento Central', true)
RETURNING id;

-- Anota el ID (ejemplo: 1)

-- Crear chacra
INSERT INTO chacras (establecimiento_id, nombre, hectareas, activo)
VALUES (1, 'Chacra Norte', 100.5, true);

-- Crear destino
INSERT INTO destinos (nombre, direccion, activo)
VALUES ('Molino Principal', 'Av. Principal 123', true);
```

### 5.2 Registrar teléfono autorizado
```sql
-- Registrar tu número de WhatsApp (reemplaza con tu número real)
INSERT INTO telefonos_empresa (empresa_id, numero, nombre_contacto, activo)
VALUES (1, '+59899123456', 'Tu Nombre', true);
```

---

## 📱 Paso 6: Configurar WhatsApp (Opcional)

### 6.1 Obtener credenciales de WhatsApp
1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Crea una app de WhatsApp Business
3. Obtén el **Token** y **Phone Number ID**

### 6.2 Configurar Webhook
1. En la configuración de WhatsApp, configura el webhook:
   - **URL**: `https://tu-backend.railway.app/webhook/whatsapp`
   - **Verify Token**: (cualquier string que quieras)
2. Suscríbete a los eventos: `messages`

### 6.3 Actualizar variables en Railway
Agrega las variables de WhatsApp en el backend:
```bash
WHATSAPP_TOKEN=EAAxxxxx
WHATSAPP_PHONE_ID=123456789
```

---

## 🎉 ¡Listo!

Tu aplicación está desplegada. Ahora puedes:

1. **Enviar un mensaje de WhatsApp** al número configurado
2. **Ver los remitos** en el panel web
3. **Gestionar configuración** desde el frontend
4. **Revisar logs** en Railway o en el panel de Logs

---

## 🔍 Troubleshooting

### Error: "CORS policy blocked"
- Verifica que `FRONTEND_URL` en el backend tenga la URL correcta del frontend
- Redeploy el backend después de cambiar variables

### Error: "Cannot connect to backend"
- Verifica que `VITE_BACKEND_BASE_URL` en el frontend sea correcto
- Asegúrate de que el backend esté corriendo (check logs en Railway)

### Error: "Supabase connection failed"
- Verifica las credenciales de Supabase
- Asegúrate de haber ejecutado las migraciones

### WhatsApp no responde
- Verifica que el webhook esté configurado correctamente
- Revisa los logs del backend en Railway
- Asegúrate de que tu número esté registrado en `telefonos_empresa`

---

## 📊 Monitoreo

### Ver logs en Railway
1. Ve a tu servicio en Railway
2. Haz clic en **"Deployments"**
3. Selecciona el deployment activo
4. Haz clic en **"View Logs"**

### Métricas
Railway te muestra automáticamente:
- CPU usage
- Memory usage
- Network traffic
- Request count

---

## 💰 Costos

Railway ofrece:
- **$5 USD gratis/mes** para hobby projects
- **$0.000231/GB-hour** para RAM
- **$0.000463/vCPU-hour** para CPU

Estimación para RemiBOT:
- Backend: ~$3-5 USD/mes
- Frontend: ~$1-2 USD/mes
- **Total: ~$4-7 USD/mes** (dentro del plan gratuito inicial)

---

## 🔄 Actualizaciones

Para actualizar tu aplicación:
1. Haz `git push` a tu repositorio
2. Railway detectará los cambios automáticamente
3. Se ejecutará un nuevo deployment

Para forzar un redeploy:
1. Ve al servicio en Railway
2. Haz clic en **"Redeploy"**

---

## 📚 Recursos Adicionales

- [Railway Docs](https://docs.railway.app/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [Supabase Docs](https://supabase.com/docs)
