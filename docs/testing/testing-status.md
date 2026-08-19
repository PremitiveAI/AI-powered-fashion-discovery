# Testing Status

**There are no automated tests in this repository, and no CI.**

This document records that fact precisely, explains what it means for anyone changing the code, and
proposes a first suite.

## Verified state

| Item | Result |
| ---- | ------ |
| Test files (`test_*.py`, `*_test.py`, `*.test.ts(x)`, `*.spec.ts(x)`) | **none** |
| Test directories (`tests/`, `__tests__/`) | **none** |
| `conftest.py`, `pytest.ini`, `tox.ini`, `setup.cfg` | **none** |
| `jest.config`, `vitest.config`, `playwright.config` | **none** |
| Test dependencies in `backend/requirements.txt` (`pytest`, `httpx`, `coverage`, …) | **none** |
| Test dependencies in `frontend/package.json` | **none** |
| `frontend/package.json` scripts | `dev`, `build`, `start`, `lint` — no `test` |
| `.github/` or any CI configuration | **does not exist** |
| Postman / REST-client collections | none in the repository |

Verification is exhaustive — a whole-repository search, excluding only `node_modules`.

## What exists instead

**Console printing.** The codebase is instrumented with `print()` statements at the points that matter
most, and these are the de-facto test harness:

| Location | Prints |
| -------- | ------ |
| `vector_db.py` | Storage path, `Total points: N`, every query text, every match with its score |
| `vision_service.describe` | The raw Gemini response when JSON parsing fails |
| `decision_engine` | Detection and arbitration progress |

None of it reaches `logs/` — it is stdout only, so it is lost the moment the process is not attached to
a terminal. See [../architecture/backend-architecture.md](../architecture/backend-architecture.md).

**Debug image output.** Two static mounts exist purely for visual inspection:

| Mount | Directory | Contents |
| ----- | --------- | -------- |
| `/debug` | `/tmp/debug_boxes` | Images with drawn bounding boxes |
| `/crops` | `/tmp/person_crops` | The person crops fed to Gemini and Cloud Vision |

For a vision pipeline this is genuinely useful — it is faster to see a wrong box than to assert on
coordinates. It is manual, but it is not worthless.

**FastAPI's interactive docs** at `http://localhost:8000/docs` — the practical way to exercise endpoints
today. Note that every request needs a `PK-apiToken` header, except `/models/*`, which needs nothing
(see [../features/phase2-models.md](../features/phase2-models.md)).

## Why this is risky here specifically

Untested code is common; a few properties of *this* codebase raise the stakes:

1. **The response envelope hides failures.** Errors return **HTTP 200** with `Success: false`. Any test —
   or monitoring check — that asserts on status codes will pass while the API is broken. Assertions must
   read the body. See [../api/overview.md](../api/overview.md).
2. **Silent degradation is designed in.** A Cloud Vision failure is caught and discarded; a malformed
   Gemini response becomes `{}`. Both produce plausible-looking empty results rather than errors, so a
   regression can run in production indefinitely without a single alarm.
3. **The vector index is destroyed at every start**, so any behaviour that depends on saved products is
   non-reproducible between runs unless the fixture re-saves them (see
   [../integrations/qdrant.md](../integrations/qdrant.md)).
4. **Every meaningful path costs money.** Image search makes 2 Gemini calls plus 1 Cloud Vision call;
   try-on makes 3 Gemini calls including image generation. A naive test suite has a per-run bill.
5. **Cross-tier contracts are already broken in four places** — Phase 2's four missing endpoints and all
   eight Phase 3 handlers. A contract test would have caught every one of them on the day it appeared.

That last point is the argument for where to start.

## Proposed first suite

Ordered by value per unit of effort. None of this has been implemented — it is a recommendation.

### 1. Contract tests (highest value, zero AI cost)

Assert that every path the frontend calls exists on the backend. The check is mechanical: collect the
`${BASE_URL}/...` targets from `frontend/app/api/**/route.ts`, collect the registered routes from
`app.routes`, and diff them.

This alone would have flagged issues 7 and 8 in [AUDIT.md](../../AUDIT.md) automatically, and it costs
nothing to run on every commit.

### 2. Envelope tests

For each endpoint: assert `Success`, `Code` and `Error` are present, that a success carries the expected
`Code`, and that a known failure carries the documented error code — `4002` for the NSFW gate, and so on.
Assert on the **body**, never the status.

### 3. Validation tests

`POST /product/save` validates category, brand, colour and image IDs before writing anything. That
ordering is a real invariant worth locking down: submit an invalid brand id and assert that no row was
created.

### 4. Pure-function unit tests (no network, no database)

The most testable code in the repository:

| Function | Module | Why it is worth testing |
| -------- | ------ | ----------------------- |
| `clean_json` | `vision_service` | Fence stripping, trailing commas, first-object extraction — pure string handling with several branches |
| `choose_best_bbox` | `decision_engine` | The Vision-over-Gemini arbitration rule |
| `vision_norm_to_resized` | `decision_engine` | Coordinate conversion, 0–1 → pixels |
| Gemini 0–1000 → pixel scaling | `decision_engine` | Off-by-scale errors here are invisible in the output |
| `SYNONYMS` matching | `decision_engine` | Would immediately expose the malformed `"makeup"` entry |

These need no mocking at all and would run in milliseconds.

### 5. Mocked integration tests

Stub `describe`, `localize_objects` and `gemini_is_safe_tryon` with recorded fixtures — the debug crops
under `/tmp/person_crops` are a ready source of realistic inputs. This gives full pipeline coverage at no
API cost, and makes the failure paths (empty Vision list, `{}` from Gemini) directly assertable, which is
otherwise almost impossible to trigger on demand.

### 6. Frontend tests

`GetApiResponse` / `PostApiResponse` in `frontend/lib/` are the single choke point for every backend call
and the obvious first target. Route handlers can be tested with mocked `fetch`.

## Recommended tooling

| Tier | Tools |
| ---- | ----- |
| Backend | `pytest`, `pytest-asyncio`, `httpx.AsyncClient` against `app`, `pytest-cov` |
| Frontend | `vitest` + `@testing-library/react`, or Jest |
| E2E (later) | Playwright |
| CI | GitHub Actions — `pytest` plus `npm run lint` and `npm run build` |

Note that `npm run build` is already a meaningful gate: it type-checks the whole frontend, and running it
in CI costs nothing extra.

## Manual verification checklist

Until a suite exists, this is the minimum to run by hand after any backend change:

1. Backend starts without error (`uvicorn app.main:app --reload` from `backend/`).
2. `GET /` returns the health response.
3. `/docs` loads and lists the expected routers.
4. Save one product; confirm `Total points: 1` in the console.
5. `POST /product/search` with a clothed photo → items returned, each with a `product_list`.
6. `POST /product/search` with an unsafe image → `Code 4002`.
7. Open `/debug/<filename>` and confirm the boxes are plausible.
8. `POST /photo/try-on` → an image is written under `/try_on`.
9. Frontend `npm run build` completes with no type errors.

Step 4 is not optional: because the index is wiped at start, a search tested before a save will
legitimately return empty product lists and look like a bug that is not there.
