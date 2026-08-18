# Documentation Index

Documentation for **AI Powered Fashion Discovery** — a FastAPI + Next.js application that detects
fashion items in a photograph, describes them with a vision LLM, matches them against a product
catalogue via vector search, and renders virtual try-on images.

Everything here is derived from the source. Where a fact could not be established from the repository it
is marked **Not verified from the current implementation.**

> **This documentation is a snapshot.** Phase 2 was under active development while it was written —
> `backend/app/main.py` changed mid-review. Treat the Phase 2 sections as current-as-of-writing.

---

## Start here

| If you want to… | Read |
| --------------- | ---- |
| Understand what the system does and how it fits together | [architecture/system-overview.md](architecture/system-overview.md) |
| Understand the AI pipeline — the core of the product | [ai/image-analysis-pipeline.md](ai/image-analysis-pipeline.md) |
| Get it running | [setup/local-development.md](setup/local-development.md) |
| Create the required Google credentials | [setup/google-cloud-credentials.md](setup/google-cloud-credentials.md) |
| Call the API | [api/overview.md](api/overview.md) |
| Know what is broken before you touch it | [../AUDIT.md](../AUDIT.md) |

---

## Architecture

| Document | Contents |
| -------- | -------- |
| [system-overview.md](architecture/system-overview.md) | Topology, BFF pattern, request lifecycle, technology inventory |
| [backend-architecture.md](architecture/backend-architecture.md) | Layering, routers, middleware, response envelope, logging |
| [frontend-architecture.md](architecture/frontend-architecture.md) | App Router structure, BFF handlers, state, pages |
| [data-flow.md](architecture/data-flow.md) | End-to-end: upload → detect → describe → match → try-on |

## AI

| Document | Contents |
| -------- | -------- |
| [image-analysis-pipeline.md](ai/image-analysis-pipeline.md) | YOLOv8 → Gemini → Vision → bbox arbitration |
| [vector-search.md](ai/vector-search.md) | Qdrant collection, embeddings, filtered search |
| [virtual-try-on.md](ai/virtual-try-on.md) | Gemini 2.5 Flash Image, safety gates |
| [prompts-and-schemas.md](ai/prompts-and-schemas.md) | Prompt contracts and the JSON shapes they produce |

## Setup

| Document | Contents |
| -------- | -------- |
| [prerequisites.md](setup/prerequisites.md) | Runtimes, services, credentials |
| [backend-setup.md](setup/backend-setup.md) | Step-by-step install with verified commands and workarounds |
| [frontend-setup.md](setup/frontend-setup.md) | Step-by-step frontend install |
| [database-setup.md](setup/database-setup.md) | Database creation, auto table creation, no-migrations caveat |
| [google-cloud-credentials.md](setup/google-cloud-credentials.md) | **How to create `vision-key.json`** |
| [environment-variables.md](setup/environment-variables.md) | Complete variable inventory, both applications |
| [local-development.md](setup/local-development.md) | Startup order, ports, verification, daily workflow |

## API reference

| Document | Contents |
| -------- | -------- |
| [overview.md](api/overview.md) | Headers, envelope, conventions |
| [error-codes.md](api/error-codes.md) | Every `Code` value and its origin |
| [products-and-gallery.md](api/products-and-gallery.md) | `/product` (7) and `/gallery` (2) |
| [masters.md](api/masters.md) | `/master` (17) |
| [stores.md](api/stores.md) | `/store` (4) |
| [photo-try-on.md](api/photo-try-on.md) | `/photo/try-on` |
| [models-phase2.md](api/models-phase2.md) | `/models` (10) and `/model` (3) — in development |

## Database

| Document | Contents |
| -------- | -------- |
| [schema.md](database/schema.md) | 21 models, columns, keys, relationships, ERD |

## Features

| Document | Status |
| -------- | ------ |
| [image-search.md](features/image-search.md) | ✅ Complete |
| [virtual-try-on.md](features/virtual-try-on.md) | ✅ Complete |
| [product-catalogue.md](features/product-catalogue.md) | ✅ Complete |
| [gallery.md](features/gallery.md) | ✅ Complete |
| [masters.md](features/masters.md) | ✅ Complete |
| [stores.md](features/stores.md) | ✅ Complete |
| [search-history.md](features/search-history.md) | ✅ Complete |
| [nearby-stores.md](features/nearby-stores.md) | ✅ Complete |
| [phase2-models.md](features/phase2-models.md) | ⚠️ In development |
| [phase3-cosmetics.md](features/phase3-cosmetics.md) | ⚠️ Frontend only |

## Integrations, security, testing, troubleshooting

| Document | Contents |
| -------- | -------- |
| [integrations/google-gemini.md](integrations/google-gemini.md) | Models used, prompts, failure modes, cost |
| [integrations/google-cloud-vision.md](integrations/google-cloud-vision.md) | Object localization, credentials |
| [integrations/qdrant.md](integrations/qdrant.md) | Embedded mode, collection lifecycle |
| [integrations/ola-maps.md](integrations/ola-maps.md) | Nearby search and reverse geocoding |
| [security/authentication-and-authorization.md](security/authentication-and-authorization.md) | The token model — and the `/models` bypass |
| [testing/testing-status.md](testing/testing-status.md) | No tests exist; proposed first suite |
| [troubleshooting/common-issues.md](troubleshooting/common-issues.md) | Symptom → cause → fix |

## Audit

| Document | Contents |
| -------- | -------- |
| [../AUDIT.md](../AUDIT.md) | 24 confirmed issues (22 open) with file-and-line evidence |

---

## Scope note

Four subsystems exist in the codebase but are **unreachable from any registered route** and are
deliberately **not** documented as features: KYC document processing (with its separate Chroma vector
store), the MariaDB `insurance_db` user layer, the employee service, and the commented-out
authentication stack. They are recorded in [../AUDIT.md](../AUDIT.md) issues 11, 15 and 16 so their
presence is explained, and nowhere else.

## Conventions

- Verified statements cite a file and, where useful, a line number.
- Endpoint tables list the request shape exactly as the Pydantic schema defines it — no invented fields.
- Response examples show the real `{Success, Code, Error}` envelope, including the fact that errors are
  returned with HTTP 200.
- Behaviour that is implemented but broken is documented as it actually behaves, cross-referenced to
  [../AUDIT.md](../AUDIT.md).
