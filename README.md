# Dr AV Capstone - AI marketing portal

A web portal where companies sign up, teach a **locally running AI model** about their products
(PDF files and notes), chat with it to get product answers and campaign copy, send campaigns to
contacts from an Excel sheet (WhatsApp, SMS, Gmail/email), and review the results in Leads and
Analytics. A Super Admin can view and download every account.

* **Frontend:** React 18 + Vite (port 5173)
* **Backend:** Python, FastAPI, Uvicorn (port 8000), JWT login, role-based access
* **Database:** SQLite (`moseta.db`, created locally - not stored in this repository)
* **AI:** Qwen2.5-0.5B-Instruct (Apache-2.0) + `multilingual-e5-small` embeddings, retrieval over each
  company's own documents; uses the NVIDIA GPU automatically when PyTorch has CUDA

The full explanation (architecture, libraries, every file) is in `Moseta_AI_Project_Guide.pdf`.

## Folder layout

| Folder | Contents |
|---|---|
| `Moseta_AI/` | AI engine (`rag_engine.py`), ingestion script, model, platform PDFs and search index |
| `master chatgpt files/Backend_for_website/Backend_for_website/` | FastAPI backend |
| `master chatgpt files/frontend_for_website/` | React website |
| `master chatgpt files/moseta_db/` | Database creation and account scripts |
| `run_moseta.py` | One-command launcher for backend + frontend |

## What is NOT in this repository (on purpose)

* `.env` files (secrets) - copy `.env.example` and fill it in
* `moseta.db` (real user accounts and password hashes) - create a fresh one, see below
* Files uploaded by companies (`Moseta_AI/uploads/`) and their private indexes
* Virtual environments, `node_modules`, caches

The model weights (`model.safetensors`, ~988 MB) are stored with **Git LFS**. Run `git lfs install`
before cloning, or download the model again with `Moseta_AI/models/download_models.py`.

## Setup

1. **Python environment** (Python 3.12) with: `fastapi`, `uvicorn`, `PyJWT`, `python-dotenv`,
   `pydantic`, `email-validator`, `python-multipart`, `openpyxl`, `torch` (use the CUDA build for a
   GPU), `transformers`, `sentence-transformers`, `numpy`, `pymupdf`, `accelerate`.
   Put it at `Moseta_AI/.venv` (the launcher looks for it there).
2. **Backend settings:** copy `Backend_for_website/Backend_for_website/.env.example` to `.env` and set
   `JWT_SECRET_KEY` (command inside the file).
3. **Create the database** (from `master chatgpt files/moseta_db/`, using the same Python):
   ```
   python init_db.py
   python rbac_setup.py
   python super_admin.py        # creates the Super Admin login
   ```
   The backend creates its own extra tables the first time it starts.
4. **Platform knowledge index:** from `Moseta_AI/` run `python ingest_documents.py`.
5. **Frontend:** in `master chatgpt files/frontend_for_website/` run `npm install`
   (copy `.env.example` to `.env` if you need to change the backend address).

## Run

```
python run_moseta.py
```

Opens http://127.0.0.1:5173. Backend API docs: http://127.0.0.1:8000/docs.

## Sending real campaigns

Campaigns are saved and recorded even without providers, but nothing is sent until credentials are
added to the backend `.env` (Gmail app password for email; Twilio for SMS and WhatsApp). Only message
people who have agreed to receive marketing messages.

## License notes

The Qwen2.5-0.5B-Instruct model is licensed under Apache-2.0 (see
`Moseta_AI/models/Qwen2.5-0.5B-Instruct/LICENSE`).
