# AI Contract Auditor

Sistema inteligente de auditoría de contratos legales que utiliza IA para automatizar la extracción de información clave desde documentos PDF y validar el cumplimiento de reglas de negocio.

## ¿Qué hace este proyecto?

1. **Extrae información automáticamente** de contratos PDF usando Google Gemini (LLM)
2. **Identifica datos clave**: partes involucradas, fechas, duración, jurisdicción
3. **Evalúa el riesgo** del contrato basado en el lenguaje utilizado
4. **Valida reglas de negocio** y marca contratos que requieren revisión humana
5. **Permite correcciones humanas** a través de una interfaz web

## Stack

- **Backend**: Python + FastAPI + LangChain + Google Gemini
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite + SQLAlchemy
- **Dataset**: CUAD (HuggingFace) - 510 contratos legales reales

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│  FastAPI Backend │────▶│     SQLite      │
│  (React + TS)   │     │    (uvicorn)     │     │  (contracts.db) │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │   PDF    │ │LangChain │ │Validation│
              │ Extractor│ │ + Gemini │ │  Agent   │
              └──────────┘ └──────────┘ └──────────┘
```

## Flujo de Procesamiento

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Upload  │───▶│ 2. Extraer  │───▶│ 3. Extraer  │───▶│ 4. Validar  │
│    PDF      │    │    Texto    │    │  Datos IA   │    │   Reglas    │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
                   ┌─────────────┐    ┌─────────────┐           │
                   │ 6. Revisar  │◀───│ 5. Guardar  │◀──────────┘
                   │  (Usuario)  │    │     BD      │
                   └─────────────┘    └─────────────┘
```

**Detalle de cada paso:**

1. **Upload PDF**: Usuario sube un contrato o se carga desde HuggingFace (dataset CUAD)
2. **Extraer Texto**: pdfplumber extrae el texto del documento PDF
3. **Extraer Datos con IA**: LangChain + Gemini analiza el texto y extrae:
   - Partes del contrato (nombres y roles)
   - Fecha efectiva
   - Duración del contrato
   - Jurisdicción
   - Score de riesgo (1-100)
4. **Validar Reglas**: El agente de validación verifica reglas de negocio
5. **Guardar en BD**: Se almacena el contrato con sus datos extraídos
6. **Revisar**: El usuario puede ver, corregir y aprobar en el frontend

## Reglas de Negocio

| Regla | Condición | Acción |
|-------|-----------|--------|
| Duración excesiva | > 24 meses | REQUIRES_HUMAN_REVIEW |
| Jurisdicción extranjera | != Chile | REQUIRES_HUMAN_REVIEW |
| Riesgo alto | risk_score > 70 | REQUIRES_HUMAN_REVIEW |

## Requisitos

- Python 3.10+
- Node.js 18+
- API Key de Google Gemini: https://makersuite.google.com/app/apikey

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/CatalinaOlivares/ai-contract-auditor.git
cd ai-contract-auditor
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y agregar tu API Key:

```
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Instalar dependencias del backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Instalar dependencias del frontend

```bash
cd frontend
npm install
cd ..
```

## Ejecución

> **Nota:** La base de datos SQLite (`contracts.db`) se crea automáticamente al iniciar el backend por primera vez.

### Terminal 1 - Backend

```bash
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

## Acceso

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Cargar contratos de prueba (HuggingFace)

```bash
# Cargar 3 contratos del dataset CUAD
curl -X POST "http://localhost:8000/api/contracts/load-sample?n=3"
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del sistema |
| POST | `/api/audit` | Subir PDF para procesar |
| GET | `/api/contracts` | Listar contratos |
| GET | `/api/contracts/{id}` | Ver contrato |
| PUT | `/api/contracts/{id}` | Editar contrato (corrección humana) |
| POST | `/api/contracts/load-sample?n=N` | Cargar N contratos de HuggingFace |

## Ejemplos de Prueba

### 1. Verificar que el sistema está funcionando

```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{"status":"healthy","database":"connected","llm_configured":true}
```

### 2. Cargar contratos de prueba desde HuggingFace

```bash
curl -X POST "http://localhost:8000/api/contracts/load-sample?n=3"
```

Esto descarga 3 contratos reales del dataset CUAD y los procesa con IA.

### 3. Ver todos los contratos

```bash
curl http://localhost:8000/api/contracts
```

### 4. Subir tu propio PDF

```bash
curl -X POST "http://localhost:8000/api/audit" \
  -F "file=@/ruta/a/tu/contrato.pdf"
```

### 5. Probar desde el navegador

1. Abrir http://localhost:5173
2. Ver la lista de contratos procesados
3. Hacer clic en un contrato para ver los detalles
4. Editar los datos extraídos si es necesario
5. Aprobar el contrato

---

# Preguntas de Arquitectura

## 1. ¿Qué técnica utilizaste para asegurar que el LLM devuelva JSON correcto?

Estrategia de 4 capas:

1. **PydanticOutputParser**: Genera instrucciones de formato automáticamente
2. **Prompt explícito**: "RESPOND ONLY WITH THE JSON"
3. **Post-procesamiento**: Maneja markdown code blocks y whitespace
4. **Fallback**: Retorna valores default con confidence=0 si falla

## 2. Si el contrato tiene 100 páginas, ¿le pasas todo al LLM?

**No.** Se trunca a 30,000 caracteres (~10,000 tokens). Para producción se usaría Map-Reduce: dividir en chunks, extraer en paralelo, y fusionar resultados.

## 3. ¿Cómo usarías las correcciones humanas para mejorar el modelo?

1. **Few-Shot dinámico**: Agregar ejemplos de correcciones recientes al prompt
2. **Fine-tuning periódico**: Con 500+ correcciones, entrenar modelo personalizado
3. **Reglas aprendidas**: Detectar patrones de error y crear reglas de post-procesamiento
