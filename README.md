
---

# 📘 README.md — Memex Prototype (Agentic LLM Wiki)

## Run Locally

### Backend

Start the upload API on port `8000`:

```bash
uv run python -m backend
```

The backend accepts uploads at `POST /upload` and stores the original files in `raw/` at the project root.

### Frontend

Start the Vite app:

```bash
cd frontend
npm install
npm run dev
```

The frontend targets `http://localhost:8000` by default. Override with `VITE_API_BASE_URL` if needed.

## 🧠 Overview

This project is a **prototype implementation of a Memex-style system** — an AI-powered pipeline where an LLM:

* Reads raw data
* Extracts knowledge
* Builds a structured wiki
* Reuses and improves knowledge over time

Inspired by:

* Memex
* LLM Wiki

The system follows a **4-phase architecture**:

1. Data Ingestion
2. LLM Processing
3. Structured Memory (Wiki)
4. Retrieval + Self-Improvement

---

# 🔄 System Workflow

```text
        ┌──────────────────────┐
        │   Input Source       │
        │ (PDF, article, chat) │
        └─────────┬────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │   RAW STORAGE        │
        │  (immutable data)    │
        └─────────┬────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  LLM Processing      │
        │  - Read source       │
        │  - Extract facts     │
        │  - Find relations    │
        └─────────┬────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │   WIKI UPDATE        │
        │  - Create pages      │
        │  - Update old pages  │
        │  - Add links         │
        └─────────┬────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  STRUCTURED MEMORY   │
        │ (connected wiki)     │
        └─────────┬────────────┘
                  │
        ┌─────────┴────────────┐
        │                      │
        ▼                      ▼
┌───────────────┐     ┌────────────────┐
│   USER QUERY  │     │ SELF-IMPROVE   │
│               │     │ (lint/reflect) │
└──────┬────────┘     └────────┬───────┘
       │                       │
       ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐
│  READ FROM WIKI      │  │ Fix gaps, conflicts  │
│ (not raw every time) │  │ add missing links    │
└─────────┬────────────┘  └─────────┬────────────┘
          │                         │
          ▼                         ▼
        ┌──────────────────────────────┐
        │   ANSWER + (OPTIONAL WRITE)  │
        │   New knowledge added        │
        └──────────────────────────────┘
```

---

# 🏗️ Architecture

### 1. Raw Layer (Source of Truth)

* Stores original data (immutable)
* Examples:

  * PDFs
  * Articles
  * Chat logs
* The system **never edits raw data** ([GitHub][1])

---

### 2. LLM Processing Layer

* Reads raw data
* Extracts:

  * Entities
  * Concepts
  * Relationships
* Updates existing knowledge base
* Acts as a **wiki maintainer** ([GitHub][2])

---

### 3. Structured Memory (Wiki)

* Markdown-based knowledge base
* Includes:

  * Summaries
  * Entity pages
  * Concept pages
  * Comparisons
* Fully maintained by the LLM ([Gist][3])

---

### 4. Retrieval + Self-Improvement

* Query system reads from **wiki (not raw data)**
* Additional processes:

  * Lint (detect inconsistencies)
  * Reflect (meta-analysis)
  * Update links & missing knowledge

---

# 🚀 Development Phases

---

## ✅ Phase 1: Data Ingestion (Current Focus)

### Goal

Build the pipeline for:

* Input collection
* Raw storage
* Basic UI + API

### Components

* Frontend:

  * Upload files (PDF, text, URLs)
  * Display ingestion status

* Backend:

  * File upload API in `backend/`
  * Storage handler (`raw/`)
  * Metadata tracking

---

## 🔜 Phase 2: LLM Processing

### Goal

Enable LLM to:

* Read sources
* Extract structured knowledge
* Identify relationships with existing data

---

## 🔜 Phase 3: Structured Memory (Wiki)

### Goal

* Generate markdown-based wiki
* Maintain:

  * Cross-links
  * Entity pages
  * Summaries

---

## 🔜 Phase 4: Retrieval + Self-Improvement

### Goal

* Build query engine
* Add:

  * Reflection loops
  * Consistency checks
  * Auto-updates

---

# 🧠 Key Idea

> “Read once → Structure → Store → Reuse → Improve”

Unlike RAG (stateless), this system:

* **Accumulates knowledge**
* **Improves over time**
* **Reduces recomputation**

---

# 📂 Proposed Folder Structure

```bash
memex-prototype/
│
├── raw/                # immutable source data
├── wiki/               # structured knowledge (LLM-generated)
├── backend/            # ingestion + APIs
├── frontend/           # UI (upload + query)
├── processing/         # LLM pipelines
├── retrieval/          # query engine
├── schema/             # LLM instructions (rules)
└── README.md
```

---
