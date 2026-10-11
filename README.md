# 🚀 CodeMentor AI — AI-Powered DSA Learning with Spaced Repetition

CodeMentor AI is an intelligent system that reviews LeetCode solutions, detects mistake patterns, and uses spaced repetition to help users **stop repeating the same errors**.

Instead of just telling whether a solution is correct, CodeMentor acts like a **personal DSA mentor** that remembers your weaknesses and forces you to revise them.

---

## ✨ What Problem Does This Solve?

While practicing DSA:

* You repeat the same mistakes across problems
* There is no memory of past errors
* Feedback is shallow (WA/TLE/AC)
* No structured revision of weak patterns

**CodeMentor AI fixes this** by:

* Reviewing code with an LLM + RAG
* Detecting mistake patterns
* Storing them
* Scheduling revisions using spaced repetition
* Providing flashcards, redo lists, and heatmaps

---

## 🧠 High-Level Architecture
![Image](public/diagram.png)

## Architecture
```mermaid
flowchart TD
    classDef client fill:#3B82F6,stroke:#1D4ED8,stroke-width:2px,color:#FFFFFF;
    classDef gateway fill:#8B5CF6,stroke:#6D28D9,stroke-width:2px,color:#FFFFFF;
    classDef broker fill:#F59E0B,stroke:#D97706,stroke-width:2px,color:#FFFFFF;
    classDef worker fill:#10B981,stroke:#047857,stroke-width:2px,color:#FFFFFF;
    classDef ai fill:#EC4899,stroke:#BE185D,stroke-width:2px,color:#FFFFFF;
    classDef db fill:#06B6D4,stroke:#0E7490,stroke-width:2px,color:#FFFFFF;
    classDef cache fill:#EF4444,stroke:#B91C1C,stroke-width:2px,color:#FFFFFF;
    classDef obs fill:#64748B,stroke:#334155,stroke-width:2px,color:#FFFFFF;
    subgraph ClientLayer ["1. Client & Presentation Layer"]
        UI["Streamlit Frontend<br/>(Port: 8501)"]:::client
    end
    subgraph GatewayLayer ["2. API Gateway & Ingress Layer"]
        API["FastAPI Gateway (Uvicorn)<br/>(Port: 18000)"]:::gateway
    end
    subgraph CachingLayer ["3. In-Memory Caching & Status"]
        Redis["Valkey / Redis<br/>(Port: 6379)<br/>• Session & Rate Limiting<br/>• Status: review:id (PENDING / PROCESSING / DONE)<br/>• Result: review:id:result"]:::cache
    end
    subgraph QueueLayer ["4. Asynchronous Task Buffering"]
        RabbitMQ["RabbitMQ Message Broker<br/>(Port: 5672 / 15672)<br/>• Direct Exchange<br/>• Durable Queue: review_queue"]:::broker
    end
    subgraph ComputeLayer ["5. Distributed Worker & AI Pipeline"]
        Worker["Celery Worker Pool<br/>(review_code_task)<br/>• Prefetch QoS = 1<br/>• Exponential Backoff Retries"]:::worker
        FAISS[("FAISS Vector Index<br/>(dsa_notes.txt)<br/>Sub-5ms Semantic Search")]:::ai
        OpenAI["OpenAI Multi-Agent Reviewer<br/>• Agent 1: Code Reviewer<br/>• Agent 2: Mistake Extractor"]:::ai
    end
    subgraph PersistenceLayer ["6. Document Persistence & Analytics"]
        Mongo[("MongoDB 7<br/>(Port: 27017)<br/>• reviews<br/>• mistakes<br/>• revision_queue<br/>• users")]:::db
    end
    subgraph ObsLayer ["7. Observability & Telemetry"]
        Prometheus["Prometheus<br/>(Port: 19090)<br/>Scrapes :8000 & :9100"]:::obs
        Grafana["Grafana Dashboards<br/>(Port: 13000)<br/>P95 Task Latency & Throughput"]:::obs
    end
    UI -- "1. POST /review_code<br/>(Code + Problem Meta)" --> API
    API -- "2. Verify JWT & Rate Limit" --> Redis
    API -- "3. Set review:id = PENDING" --> Redis
    API -- "4. Publish review_code_task" --> RabbitMQ
    API -- "5. Return HTTP 202 Accepted<br/>(review_id)" --> UI
    UI -. "6. Poll GET /review_status/:id<br/>(Every 2s)" .-> API
    API -. "7. O(1) Cache Lookup" .-> Redis
    RabbitMQ -- "8. Consume Task" --> Worker
    Worker -- "9. Update review:id = PROCESSING" --> Redis
    Worker -- "10. Query Top-K DSA Context" --> FAISS
    FAISS -. "Relevant Concepts" .-> Worker
    Worker -- "11. Prompt (Context + Code)" --> OpenAI
    OpenAI -. "Review + Structured JSON Mistakes" .-> Worker
    Worker -- "12. Persist Reviews, Mistakes & Spaced Schedule" --> Mongo
    Worker -- "13. Set review:id = DONE & Cache Result" --> Redis
    Worker -- "14. Send ACK" --> RabbitMQ
    Prometheus -. "Scrapes API Metrics" .-> API
    Prometheus -. "Scrapes Task Latency (:9100)" .-> Worker
    Grafana -. "Queries Metrics" .-> Prometheus
```
---

## ⚙️ Tech Stack (and why)

| Tech                 | Purpose                                 |
| -------------------- | --------------------------------------- |
| FastAPI              | High-performance API for async workflow |
| Streamlit            | Simple interactive frontend             |
| RabbitMQ             | Reliable message broker for reviews     |
| Celery               | Background task processing              |
| Valkey (Redis)       | Review status cache for polling         |
| MongoDB              | Mistake history, revision scheduling    |
| FAISS                | Semantic retrieval over DSA notes (RAG) |
| OpenAI               | Code review agent                       |
| Prometheus + Grafana | Production-grade observability          |
| Docker Compose       | Multi-service reproducible environment  |


---

## 🔁 Review Flow (Async)

1. User submits code
2. FastAPI generates `review_id`
3. Task pushed to RabbitMQ
4. Celery worker processes review (RAG + LLM)
5. Mistake stored in MongoDB
6. Result stored in Redis
7. Frontend polls `/review_status` until done

This ensures:

* Non-blocking API
* Scalable review pipeline
* Clean separation of concerns

---

## 📊 Observability (Real Metrics)

The system tracks:

* API request rate
* API p95 latency per endpoint
* Reviews processed per second
* Review processing time (p95)

These are visualized in Grafana.

> Add your Grafana screenshot here

---

## 🧩 Features

* AI code review using RAG + LLM
* Mistake pattern detection
* Spaced repetition revision queue
* Flashcards from past mistakes
* Topic heatmap of weaknesses
* Redo list for problematic questions
* Fully asynchronous processing
* Observable system health

---

## ▶️ How to Run Locally

### Prerequisites

* Docker
* OpenAI API Key in `.env`

### Start the system

```bash
docker-compose up --build
```

### Access

| Service      | URL                                              |
| ------------ | ------------------------------------------------ |
| Streamlit UI | [http://localhost:8501](http://localhost:8501)   |
| FastAPI      | [http://localhost:18000](http://localhost:18000) |
| Prometheus   | [http://localhost:19090](http://localhost:19090) |
| Grafana      | [http://localhost:13000](http://localhost:13000) |

---

## 📈 Scaling Strategy

To scale reviews:

* Add more Celery workers
* RabbitMQ distributes tasks automatically
* FastAPI remains stateless
* No code changes required

---

## 🛡️ Reliability

* Celery retries with backoff
* Redis for idempotent status tracking
* Queue prevents request loss
* Structured logging
* Metrics for detecting bottlenecks

---

## 📚 System Design

See detailed design here:
👉 `SYSTEM_DESIGN.md`

---

## 🎯 Key Learnings

This project demonstrates:

* Designing async AI systems
* Queue-based architecture
* Observability in microservices
* RAG + LLM integration
* Scalable backend design


