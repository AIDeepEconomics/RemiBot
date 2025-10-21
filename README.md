# RemiBOT 🤖

Sistema inteligente de gestión de remitos arroceros mediante WhatsApp con contexto personalizado por empresa.

## 🎯 Características Principales

- **Chatbot WhatsApp con IA**: Conversación natural usando LLMs (Claude/GPT)
- **Contexto Personalizado**: Cada empresa tiene su propio catálogo de establecimientos y chacras
- **Control de Acceso por Teléfono**: Solo números autorizados pueden crear remitos
- **Generación Automática de QR**: Cada remito incluye código QR para trazabilidad
- **Panel Web Administrativo**: Gestión completa de remitos, configuración y logs

## 📁 Arquitectura

- `backend/`: API FastAPI con webhooks, servicios de LLM y gestión de remitos
- `frontend/`: Panel web React + TypeScript + Vite
- `infra/supabase/`: Migraciones SQL para PostgreSQL en Supabase

## Componentes principales

### Backend (Python + FastAPI)

- `app/main.py`: Punto de entrada y configuración de la instancia FastAPI.
- `app/api/`: Conjunto de routers (`webhook`, `remitos`, `config`).
- `app/core/`: Servicios auxiliares (LLM, QR, remitos, settings).
- `app/models/`: Modelos Pydantic para tipado de payloads y respuestas.

Dependencias claves en `backend/requirements.txt`:

- `fastapi`, `uvicorn` para API HTTP.
- `httpx` para integraciones REST (WhatsApp, LLMs).
- `supabase` para persistencia (future work: conexión real a Supabase).
- `qrcode`, `pillow` para generación de QR (placeholder actual).

### Frontend (Vite + React + TS)

- `src/App.tsx`: Define rutas principales (`Inicio`, `Remitos`, `Configuración`, `Documentación`, `Logs`).
- `src/components/AppLayout.tsx`: Layout base con navegación lateral.
- `src/views/`: Vistas iniciales con placeholders y estructura de formularios/tablas.
- `src/styles.css`: Estilos globales con énfasis en una UI moderna.

Scripts principales:

- `npm run dev`: arranca servidor de desarrollo Vite.
- `npm run build`: compila TypeScript y genera bundle productivo.
- `npm run lint`: ejecuta ESLint.

Variables de entorno esperadas:

- `VITE_BACKEND_BASE_URL` (client-side) para apuntar al backend.

### Base de Datos (Supabase)

**Migraciones:**
- `0001_init.sql`: Esquema base (empresas, establecimientos, chacras, destinos, remitos, configuraciones, logs)
- `0002_telefonos_empresa.sql`: Sistema de autorización por teléfono con normalización automática

**Tablas principales:**
- `empresas`: Empresas del sistema
- `establecimientos`: Establecimientos por empresa
- `chacras`: Chacras asociadas a establecimientos
- `destinos`: Destinos de entrega
- `remitos`: Registro de remitos con QR y trazabilidad
- `telefonos_empresa`: Control de acceso por número de WhatsApp
- `configuraciones`: Claves API y configuración del sistema
- `logs`: Auditoría de eventos

## 🔐 Sistema de Contexto Personalizado

El sistema identifica automáticamente la empresa del usuario por su número de WhatsApp:

1. **Normalización flexible**: Acepta números en cualquier formato (+598 99 123 456, 59899123456, etc.)
2. **Búsqueda inteligente**: Busca con variaciones (con/sin código de país)
3. **Prompts contextuales**:
   - Números registrados → Reciben catálogo de su empresa (establecimientos y chacras)
   - Números NO registrados → Mensaje educado explicando que deben contactar al administrador

## 🚀 Deployment en Producción (Railway)

RemiBOT está desplegado en **Railway** con dos servicios independientes:

### 🔧 Backend (FastAPI)
- **URL**: `https://remibot-production-e609.up.railway.app`
- **Documentación API**: `/docs`
- **Health Check**: `/`
- **Configuración**:
  - Root Directory: `backend`
  - Builder: Nixpacks (Python 3.12)
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 🎨 Frontend (React + Vite)
- **Configuración**:
  - Root Directory: `frontend`
  - Builder: Nixpacks (Node.js 20)
  - Build: `npm install && npm run build`
  - Start Command: `npx serve -s dist -p $PORT`

### 📋 Pasos para Desplegar

1. **Crear proyecto en Railway** desde GitHub
2. **Configurar Backend**:
   - Root Directory: `backend`
   - Variables de entorno: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, etc.
   - Generar dominio público
3. **Configurar Frontend**:
   - Root Directory: `frontend`
   - Variable: `VITE_BACKEND_BASE_URL` (URL del backend)
   - Generar dominio público
4. **Actualizar Backend**:
   - Variable: `FRONTEND_URL` (URL del frontend)
   - Redeploy

**Guía completa**: Ver [`DEPLOYMENT.md`](./DEPLOYMENT.md)

---

## 💻 Desarrollo Local

### Requisitos Previos

- Python 3.12+
- Node.js 18+
- Cuenta en Supabase
- Claves API de OpenAI o Anthropic (Claude)

### Backend

```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con la URL del backend

# Iniciar servidor de desarrollo
npm run dev
```

### Base de Datos

1. Crear proyecto en [Supabase](https://supabase.com)
2. Ejecutar migraciones en el SQL Editor:
   - `infra/supabase/migrations/0001_init.sql`
   - `infra/supabase/migrations/0002_telefonos_empresa.sql`
3. Copiar credenciales a `backend/.env`

## 📡 API Endpoints

### Webhook
- `POST /webhook/whatsapp` - Recibe mensajes de WhatsApp

### Remitos
- `GET /remitos` - Lista todos los remitos
- `GET /remitos/{id}` - Obtiene un remito específico
- `POST /remitos` - Crea un remito manualmente

### Teléfonos
- `GET /telefonos/empresa/{id}` - Lista teléfonos de una empresa
- `POST /telefonos/` - Registra un nuevo teléfono
- `DELETE /telefonos/{id}` - Desactiva un teléfono
- `GET /telefonos/check/{numero}` - Verifica empresas asociadas

### Configuración
- `GET /config` - Obtiene configuración actual
- `PUT /config` - Actualiza configuración

### Logs
- `GET /logs` - Obtiene logs del sistema

## 🔧 Variables de Entorno

### Backend (`backend/.env`)

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
SUPABASE_ANON_KEY=xxx

# LLM APIs
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# WhatsApp (opcional)
WHATSAPP_TOKEN=xxx
WHATSAPP_PHONE_ID=xxx
WHATSAPP_API_VERSION=v18.0

# General
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
```

### Frontend (`frontend/.env`)

```env
VITE_BACKEND_BASE_URL=http://localhost:8000
```

## 📦 Archivos de Configuración para Railway

El proyecto incluye archivos específicos para el deployment en Railway:

### Backend
- `backend/railway.json`: Configuración de build y deploy
- `backend/Procfile`: Comando de inicio alternativo
- `backend/runtime.txt`: Versión de Python (3.12.0)

### Frontend
- `frontend/railway.json`: Configuración de deploy
- `frontend/nixpacks.toml`: Configuración de build con Nixpacks

Estos archivos permiten que Railway detecte automáticamente cómo construir y ejecutar cada servicio.

---

## 🔄 CI/CD

Railway detecta automáticamente los cambios en la rama `main` de GitHub y redespliega los servicios afectados. No se requiere configuración adicional.

---

## 📝 Licencia

AI Deep Economics SAS 2025. Todos los derechos reservados
