# RepoMind

AI‑powered GitHub Repository Intelligence Assistant.

- Backend: Python FastAPI
- Vector store: Qdrant (Docker Compose)
- LLM: Open‑source FLAN‑T5
- Embeddings: sentence‑transformers/paraphrase‑MPNet‑base‑v2
- Frontend: React + Vite (TypeScript)
- Auth: GitHub OAuth

## Quick start (development)
```bash
# Clone this repo
git clone <repo-url> .

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev
```
```
