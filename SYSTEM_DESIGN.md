# CodeMentor AI — System Design

## 1. Problem Statement

Learning Data Structures & Algorithms from platforms like LeetCode is inefficient because:

* Users repeat the same mistakes across problems
* There is no structured feedback on *why* a solution is wrong
* There is no memory of past mistakes
* No spaced repetition for weak patterns

**CodeMentor AI** solves this by acting as an AI reviewer that:

* Reviews user solutions
* Detects mistake patterns
* Stores them
* Uses spaced repetition to force revision
* Provides flashcards, heatmaps, and redo lists

---

## 2. High-Level Architecture

![Image](https://miro.medium.com/v2/resize%3Afit%3A1200/1%2AYwDZ4-ZLxwWy3BRDsHg83A.png)

![Image](https://miro.medium.com/v2/resize%3Afit%3A1400/1%2AR5uEj4as1GAT4OaAWKzz7A.png)

![Image](https://knowledge.dataiku.com/latest/_images/rag-pipeline.png)

![Image](https://miro.medium.com/v2/resize%3Afit%3A537/1%2A15RRWQMoRI6qdGEzPiWIJQ.png)

```
User (Streamlit UI)
        │
        ▼
     FastAPI
        │
        ▼
    RabbitMQ Queue
        │
        ▼
     Celery Worker
        │
        ▼
 RAG (FAISS) + OpenAI Review
        │
        ▼
      MongoDB
        │
        ▼
  Streamlit Dashboard
```

**Observability Layer**

```
Prometheus  ← scrapes →  FastAPI + Worker
Grafana     ← queries →  Prometheus
```

---

## 3. Why Asynchronous Architecture?

LLM + RAG review takes **8–15 seconds**.

If done synchronously:

* UI blocks
* API times out
* Poor UX

So the system uses:

* FastAPI → publishes task to RabbitMQ
* Celery Worker → processes review in background
* Redis (Valkey) → stores review status
* Frontend polls `/review_status`

This ensures:

* Non-blocking API
* Scalable review pipeline
* Clean separation of concerns

---

## 4. Component Responsibilities

| Component      | Responsibility                                    |
| -------------- | ------------------------------------------------- |
| Streamlit      | User interface, polling review status             |
| FastAPI        | Auth, problem fetch, task publish, analytics APIs |
| RabbitMQ       | Message broker for async reviews                  |
| Celery Worker  | Runs RAG + LLM review pipeline                    |
| Valkey (Redis) | Review status & result cache                      |
| MongoDB        | Mistake history, revision queue, analytics        |
| FAISS          | Vector search over DSA notes                      |
| OpenAI         | Code review agent                                 |
| Prometheus     | Metrics collection                                |
| Grafana        | Visualization & monitoring                        |

---

## 5. Review Flow (Step-by-step)

1. User submits code
2. FastAPI generates `review_id`
3. Task pushed to RabbitMQ
4. Worker consumes task
5. RAG retrieves relevant DSA context
6. LLM reviews code
7. Mistake pattern stored in MongoDB
8. Result saved in Redis
9. Frontend polling detects completion

---

## 6. Observability & Monitoring

The system exposes:

* API request rate
* API latency (p95)
* Celery task rate
* Review processing time (p95)

This allows monitoring:

* System load
* Worker performance
* Bottlenecks in review pipeline

*(Grafana screenshot here)*

---

## 7. Failure Handling & Reliability

* Celery tasks configured with retries and backoff
* Redis used for idempotent status tracking
* Queue prevents request loss
* Logging across API and worker
* Metrics for detecting slowdowns

---

## 8. Scaling Strategy

To scale reviews:

* Increase number of Celery workers
* RabbitMQ distributes tasks automatically
* FastAPI remains stateless
* MongoDB handles growing mistake history
* FAISS index reusable across workers

No code changes required for horizontal scaling.

---

## 9. Why These Technologies?

| Tech               | Reason                                 |
| ------------------ | -------------------------------------- |
| FastAPI            | High performance, async-friendly       |
| RabbitMQ           | Reliable message broker                |
| Celery             | Mature async task processing           |
| Redis              | Fast status cache for polling          |
| MongoDB            | Flexible schema for mistake patterns   |
| FAISS              | Efficient semantic retrieval           |
| Prometheus/Grafana | Production-grade observability         |
| Docker             | Reproducible multi-service environment |

---

## 10. Key Learnings

This project demonstrates:

* Designing async AI systems
* Queue-based architecture
* Observability in microservices
* RAG + LLM integration
* Scalable backend design
