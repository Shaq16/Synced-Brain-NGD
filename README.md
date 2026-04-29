# 🧠 Synced Brain — RAG-Ops AI Second Brain

> A production-grade, self-healing knowledge base. Drop files into `knowledge/`, push to GitHub, and your AI is updated — automatically, with zero stale data.

---

## What it does

| Layer | Technology | Role |
|---|---|---|
| **Vector DB** | Milvus (standalone) | Semantic memory — stores chunk embeddings |
| **Embeddings** | Cohere `embed-english-v3.0` | Converts text → 1024-dim vectors |
| **LLM** | Gemini 1.5 Flash | Generates grounded answers from retrieved context |
| **Sync Engine** | Python + GitHub Actions | Keeps Milvus in perfect sync with `knowledge/` |
| **API** | FastAPI | `/health` + `/query` endpoints |
| **UI** | React + Vite | Chat interface with citations and source filters |

---

## Architecture Overview

```
 git push
    │
    ▼
GitHub Actions (sync-brain.yml)
    │  git diff → find changed .md / .pdf files
    │
    ▼
sync.py  (Sync Engine)
    ├── parse_file()     → raw text per page
    ├── chunk_pages()    → 800-char overlapping chunks
    ├── cohere.embed()   → 1024-dim vectors
    └── milvus_store.py  → upsert / delete / query
          │
          ▼
    Milvus (synced_brain_chunks collection)
          │
          ▼
    FastAPI  /query
    ├── embed question (Cohere)
    ├── vector search (Milvus HNSW)
    ├── assemble context
    └── Gemini answer + citations
          │
          ▼
    React UI (chat + citations)
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node 18+
- API keys: [Cohere](https://cohere.com) + [Google AI Studio](https://aistudio.google.com)

---

### 1. Start Milvus locally

```bash
docker compose up -d
```

This starts Milvus standalone, etcd, MinIO, and Attu (Milvus UI at http://localhost:8080).

Wait ~30s for Milvus to become healthy:
```bash
docker compose ps   # all services should show "healthy"
```

---

### 2. Configure backend

```bash
cd backend
cp .env.example .env
# Edit .env and fill in your COHERE_API_KEY and GOOGLE_API_KEY
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

### 3. Add knowledge files

```bash
# Put any .md or .pdf files in knowledge/
cp my-notes.md knowledge/
cp paper.pdf   knowledge/research/
```

Run the sync engine manually (first time):
```bash
python -m backend.app.sync.sync
# Output: added=N  modified=0  deleted=0  unchanged=0
```

---

### 4. Start the backend

```bash
# From repo root
uvicorn backend.app.main:app --reload --port 8000
```

Test it:
```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What do my notes say about X?", "top_k": 5}'
```

---

### 5. Start the frontend

```bash
cd frontend
cp .env.example .env      # VITE_BACKEND_URL=http://localhost:8000
npm install
npm run dev
# Open http://localhost:5173
```

---

## Automated Sync via GitHub Actions

Every `git push` to `main` that touches `knowledge/` triggers the sync workflow.

### Setup (one-time)

Add these **Repository Secrets** (Settings → Secrets → Actions):

| Secret | Description |
|---|---|
| `MILVUS_HOST` | Hostname of your hosted Milvus instance |
| `MILVUS_PORT` | Default: `19530` |
| `MILVUS_COLLECTION` | Default: `synced_brain_chunks` |
| `COHERE_API_KEY` | Your Cohere API key |
| `GOOGLE_API_KEY` | Your Google AI API key |

> **Note:** GitHub-hosted runners cannot reach `localhost`. Use a hosted Milvus (e.g., [Zilliz Cloud](https://zilliz.com/cloud) free tier) or configure a self-hosted runner that can reach your Milvus.

### Manual trigger

```
GitHub → Actions → 🧠 Sync Brain → Run workflow
```

---

## Project Structure

```
.
├── knowledge/                        ← Your source-of-truth files (.md, .pdf)
│   └── README.md
│
├── backend/
│   ├── app/
│   │   ├── main.py                   ← FastAPI app (GET /health, POST /query)
│   │   ├── ingestion/
│   │   │   ├── parsers.py            ← .md and .pdf text extraction
│   │   │   └── chunking.py           ← LangChain text splitter wrapper
│   │   ├── vectorstore/
│   │   │   └── milvus_store.py       ← All Milvus ops (connect, upsert, delete, search)
│   │   ├── sync/
│   │   │   ├── sync.py               ← Sync engine (full reconcile + git-diff mode)
│   │   │   └── hashing.py            ← Deterministic IDs and content hashing
│   │   └── tests/
│   │       └── test_sync_and_query.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── App.tsx                   ← Chat UI with citations + filters
│       ├── App.css
│       └── api.ts                    ← queryBrain() / checkHealth()
│
├── scripts/
│   └── smoke_test.sh                 ← Quick end-to-end sanity check
│
├── .github/workflows/
│   └── sync-brain.yml                ← RAG-Ops CI pipeline
│
└── docker-compose.yml                ← Milvus + etcd + MinIO + Attu
```

---

## Milvus Schema

Collection: `synced_brain_chunks`

| Field | Type | Description |
|---|---|---|
| `id` | VARCHAR (PK) | `base64url(sha256(path)):chunk_index` |
| `embedding` | FLOAT_VECTOR (1024) | Cohere embedding |
| `source` | VARCHAR | File path, e.g. `knowledge/ops/runbook.md` |
| `content_hash` | VARCHAR | SHA-256 of file — change detection |
| `chunk_index` | INT64 | Position within the file |
| `chunk_text` | VARCHAR | The actual chunk content |
| `last_modified` | VARCHAR | Unix timestamp string |
| `doc_type` | VARCHAR | `md` or `pdf` |
| `page` | INT64 | PDF page number (-1 for Markdown) |

Index: **HNSW** (M=16, efConstruction=200) with **COSINE** metric.

---

## Sync Engine Logic

The sync engine (`sync.py`) handles three operations to prevent "vector drift":

| State | Detection | Action |
|---|---|---|
| **File Added** | Not in Milvus | Parse → embed → upsert |
| **File Modified** | `content_hash` differs | Delete old chunks → upsert new |
| **File Deleted** | In Milvus but not on disk | `delete_by_source()` |
| **Unchanged** | Same hash | Skip (idempotent) |

---

## Environment Variables

**Backend:**

| Variable | Default | Description |
|---|---|---|
| `MILVUS_HOST` | `localhost` | Milvus host |
| `MILVUS_PORT` | `19530` | Milvus gRPC port |
| `MILVUS_COLLECTION` | `synced_brain_chunks` | Collection name |
| `KNOWLEDGE_DIR` | `knowledge` | Path to knowledge folder |
| `COHERE_API_KEY` | — | Cohere API key |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `ALLOW_ORIGINS` | `*` | CORS allowed origins |

**Frontend:**

| Variable | Default | Description |
|---|---|---|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend URL |

---

## Testing

```bash
# Smoke test (requires running Milvus + backend)
bash scripts/smoke_test.sh

# Pytest integration test
pytest backend/app/tests/test_sync_and_query.py -v
```

---

## Definition of Done ✅

- [x] Milvus vector store integration (`milvus_store.py`)
- [x] Sync engine with add/modify/delete reconciliation (`sync.py`)
- [x] New `/query` endpoint with Milvus retrieval + Gemini answer + citations
- [x] Frontend updated — query input, chat, citation cards, source filters
- [x] `knowledge/` folder with seeding README
- [x] Docker Compose for Milvus local dev
- [x] GitHub Actions workflow (`sync-brain.yml`)
- [x] README with full setup + run steps


---

## 🚀 DevOps Setup — Jenkins + Docker (CI/CD Pipeline)

This project implements a **Continuous Integration and Continuous Deployment (CI/CD)** pipeline using Jenkins and Docker.

---

### 🔁 CI/CD Workflow

```
GitHub (Code Push)
    ↓
Jenkins Pipeline Trigger
    ↓
Build Docker Image (CI)
    ↓
Run / Test Backend (CI)
    ↓
Deploy Container (CD)
    ↓
Application running on localhost:8000
```

---

### ⚙️ Tools Used

| Tool | Purpose |
|------|---------|
| Jenkins | CI/CD automation |
| Docker | Containerization & deployment |
| GitHub | Source code management |
| FastAPI | Backend service |

---

### 🐳 Docker Setup

The application is containerized using Docker.

**Build Image**
```bash
docker build -t synced-brain .
```

**Run Container**
```bash
docker run -d -p 8000:8000 --name synced-brain-container synced-brain
```

---

### ⚡ Jenkins Setup

Jenkins is run using Docker:

```bash
docker run -d -p 9090:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name jenkins jenkins/jenkins:lts
```

Access Jenkins at: `http://localhost:9090`

---

### 🧪 CI/CD Pipeline (Jenkinsfile)

The pipeline automates build, test, and deployment:

```groovy
pipeline {
    agent any

    stages {

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t synced-brain .'
            }
        }

        stage('Test / Run Backend') {
            steps {
                sh 'docker run --rm synced-brain'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker rm -f synced-brain-container || true
                docker run -d -p 8000:8000 --name synced-brain-container synced-brain
                '''
            }
        }
    }
}
```

---

### 🔄 Continuous Integration (CI)

- ✅ Automatically builds Docker image
- ✅ Runs backend to verify functionality
- ✅ Detects errors (e.g., missing dependencies)

> **Trigger:** Manual (`Build Now`) or GitHub push (if webhook configured)

---

### 🚀 Continuous Deployment (CD)

- ✅ Automatically stops old container
- ✅ Deploys new container with latest code
- ✅ Application is immediately available after pipeline completes

> No manual deployment required.

---

### ⚡ Optimization

- Docker layer caching is used
- Dependencies install only when `requirements.txt` changes
- Faster builds compared to traditional CI setups

---

### 🧪 Validation Steps

1. Modify backend code (e.g., update an API response)
2. Push changes to GitHub
3. Trigger the Jenkins pipeline
4. Verify:
   - Build success in Jenkins console logs
   - Container restarted (`docker ps`)
   - Updated output visible at `http://localhost:8000`

---

### 📸 Demo Evidence

- Jenkins Console Output (build, test, deploy stages)
- Running container (`docker ps`)
- Application response from browser

---

### ⚠️ Notes

- Webhooks are not configured due to localhost limitations
- Pipeline is triggered manually in Jenkins
- Deployment is local (suitable for academic demonstration)
