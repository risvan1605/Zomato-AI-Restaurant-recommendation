# Phase-wise Implementation Plan - Restaurant Recommendation System

This implementation plan details a structured phase-by-phase approach for building the AI-powered Zomato-style restaurant recommendation system. The implementation uses a **filter-first, reason-second** design strategy, with **Groq** as the sole LLM provider, **FastAPI** for the backend REST API, and **Next.js** (React) for the frontend user interface.

## User Review Required

> [!IMPORTANT]
> The system downloads the Hugging Face dataset on the first run, which is ~574 MB. A local Parquet cache will be created under `data/` or `cache/` to ensure sub-second startup times on subsequent runs.

> [!IMPORTANT]
> We will configure **Groq** (`llama-3.3-70b-versatile`) as the default model using its native JSON mode or structural schemas to ensure clean JSON extraction for UI rendering, with `llama-3.1-8b-instant` as a fallback.

> [!WARNING]
> **Tech Stack Change**: This plan replaces the original Streamlit frontend with a **FastAPI + Next.js** architecture. The Python backend now exposes RESTful API endpoints consumed by a separate Next.js (React) frontend application. This introduces a multi-process development workflow (backend + frontend dev servers running concurrently).

## Open Questions

> [!NOTE]
> 1. **Budget Thresholds Calibration**: The default tiers defined in the architecture are: Low (≤ ₹500), Medium (₹501–₹1500), and High (> ₹1500) for two people. Do you want these calibrated or customized after parsing the dataset distributions?
> 2. **Reviews Inclusion**: The raw `reviews_list` text is extremely large (up to 1.28MB). The proposed plan excludes full reviews from the LLM prompt to prevent context limit errors and latency issues. Is this acceptable, or should we include a summarized/sliced subset of reviews?
> 3. **Next.js Deployment**: Should the Next.js frontend be configured for static export (`output: 'export'`) for simple hosting, or SSR/ISR mode for dynamic server-side rendering?

---

## Proposed Changes

We will build the project inside the workspace directory: `/Users/ris/Cursor/Restaurent Recommendation system`.
- **Backend (Python/FastAPI)**: Lives under `src/` (existing structure).
- **Frontend (Next.js)**: Lives under `frontend/` (new directory).

### Updated Project Structure

```
Restaurent Recommendation system/
├── docs/
│   ├── context.md
│   ├── architecture.md
│   ├── edgecase.md
│   └── implementation_plan.md
├── src/                               # Python Backend (FastAPI)
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   ├── models/
│   │   ├── restaurant.py
│   │   ├── preferences.py
│   │   └── recommendation.py
│   ├── data/
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   └── repository.py
│   ├── services/
│   │   ├── filter.py
│   │   ├── prompt_builder.py
│   │   ├── llm_client.py
│   │   ├── recommendation.py
│   │   ├── response_validator.py
│   │   ├── validator.py
│   │   ├── candidate_mapper.py
│   │   └── errors.py
│   └── api/                           # [NEW] FastAPI routes & schemas
│       ├── __init__.py
│       ├── main.py                    # FastAPI app factory & lifespan
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── recommend.py           # POST /api/v1/recommend
│       │   ├── metadata.py           # GET /api/v1/locations, cuisines, etc.
│       │   └── health.py             # GET /api/v1/health
│       ├── schemas.py                 # Request/Response Pydantic models
│       ├── dependencies.py            # Dependency injection (repo, services)
│       └── middleware.py              # CORS, rate limiting, error handlers
├── frontend/                          # [NEW] Next.js Frontend
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout with fonts & metadata
│   │   │   ├── page.tsx               # Home page
│   │   │   └── globals.css            # Global design system
│   │   ├── components/
│   │   │   ├── HeroSection.tsx
│   │   │   ├── PreferencePanel.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── ResultsGrid.tsx
│   │   │   ├── FilterSummary.tsx
│   │   │   ├── SkeletonCards.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ErrorBanner.tsx
│   │   ├── hooks/
│   │   │   └── useRecommendations.ts  # API call hook with loading/error states
│   │   ├── lib/
│   │   │   └── api.ts                 # API client for FastAPI backend
│   │   └── types/
│   │       └── index.ts               # TypeScript types mirroring API schemas
│   └── ...
├── tests/
│   ├── test_filter.py
│   ├── test_preprocessor.py
│   ├── test_recommendation.py
│   ├── test_response_validator.py
│   ├── test_error_handling.py
│   └── test_api.py                    # [NEW] FastAPI endpoint tests
├── data/                              # cached parquet (gitignored)
├── .env.example
├── requirements.txt
└── README.md
```

---

### Phase 1: Environment Setup & Project Shell ✅
Setup python dependencies, environment configurations, and core dataclass models.

#### [NEW] [requirements.txt](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/requirements.txt)
Define external Python dependencies:
- `pandas`
- `datasets`
- `pydantic`
- `pydantic-settings`
- `python-dotenv`
- `groq`
- `fastapi`
- `uvicorn[standard]`
- `pytest`
- `httpx` (for FastAPI test client)

#### [NEW] [.env.example](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/.env.example)
Define environment variables:
- `LLM_PROVIDER` (default `groq`)
- `LLM_MODEL` (default `llama-3.3-70b-versatile`)
- `GROQ_API_KEY`
- `MAX_CANDIDATES` (default `20`)
- `FRONTEND_URL` (default `http://localhost:3000`, used for CORS)

#### [NEW] [src/config.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/config.py)
A settings management file (utilizing `pydantic-settings`) to read from `.env` and load configurations with validations:
- `HF_DATASET_NAME`
- `BUDGET_THRESHOLDS`
- `MAX_CANDIDATES_FOR_LLM`
- `TOP_K_RECOMMENDATIONS`
- `GROQ_MODEL`
- `GROQ_API_KEY`
- `GROQ_TEMPERATURE`
- `FRONTEND_URL` (for CORS origin allowlist)

#### [NEW] [src/models/restaurant.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/models/restaurant.py)
Define the canonical `Restaurant` model schema using Pydantic or Dataclasses.

#### [NEW] [src/models/preferences.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/models/preferences.py)
Define typing schema for `UserPreferences` containing location, budget tier, optional single cuisine, min rating, and additional free-form details.

#### [NEW] [src/models/recommendation.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/models/recommendation.py)
Define validation structures for `Recommendation` and the metadata-nested `RecommendationResponse`.

---

### Phase 2: Ingestion & Preprocessing ✅
Implement loading data from Hugging Face and preprocessing data columns into structured formats.

#### [NEW] [src/data/loader.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/data/loader.py)
Uses Hugging Face `datasets` to pull the Zomato dataset and save/load it as local Parquet in `data/` cache.

#### [NEW] [src/data/preprocessor.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/data/preprocessor.py)
Implements cleaning logic:
- Parse ratings (e.g. `"4.1/5"` -> `4.1` float, handling `"NEW"` and `"-"` as `None`).
- Clean `approx_cost(for two people)` by parsing string to integer.
- Classify budget into Low (≤ 500), Medium (501–1500), High (> 1500) tiers.
- Convert comma-separated `cuisines` string to list of cuisines.
- Normalize location and city names.

#### [NEW] [src/data/repository.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/data/repository.py)
Provides catalog operations:
- Retrieve all rows as processed `Restaurant` models.
- Get unique locations/cuisines list to populate select dropdowns.

---

### Phase 3: Filtering Engine ✅
Build the integration layer to filter data deterministically.

#### [NEW] [src/services/filter.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/filter.py)
Preference validator and filter engine implementing cascading constraints:
1. Locality or City matching.
2. Budget Tier matching.
3. Min Rating threshold.
4. Optional cuisine matching.
5. Sort by rating desc + votes desc, and truncate to top K candidates (default 15–20).
6. Auto-relaxation mechanism if zero candidates remain (cuisine -> budget -> rating).

---

### Phase 4: Prompt Construction & Groq Client Integration ✅
Connect with Groq APIs, render prompts, and run validation.

#### [NEW] [src/services/prompt_builder.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/prompt_builder.py)
Formats preferences and candidate JSON lists into a structured XML/Jinja2 template. Instructs the model to output valid JSON matching the schema and restrict itself to the candidates.

#### [NEW] [src/services/llm_client.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/llm_client.py)
Concrete client wrapper calling Groq's official Python SDK with `llama-3.3-70b-versatile`. Enables JSON output formatting, timeout controls, and backoff retries.

#### [NEW] [src/services/recommendation.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/recommendation.py)
The central orchestrator orchestrating:
`Preferences -> filter -> prompt_builder -> llm_client -> ResponseParser -> RecommendationEnricher -> RecommendationResponse`.
Includes metric-based fallback logic (rating/votes desc) in case of Groq API failures.

---

### Phase 5: Backend Hardening & Edge-Case Resilience
Addresses all missing backend hardening identified from `architecture.md` §8 and `edgecase.md`. This phase makes the backend production-ready before the UI is built on top.

#### [MODIFY] [loader.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/data/loader.py)
**Corrupted cache recovery** (edgecase.md §1):
- Wrap `pd.read_parquet()` in a try/except block. If the cached Parquet file is corrupted (raises `ArrowInvalid`, `ParquetException`, etc.), automatically delete the corrupted file and trigger a fresh download from Hugging Face.
- Add a clear log message: `"Cache corrupted, re-downloading..."`.

**Schema validation on load** (edgecase.md §1):
- After loading, validate that mandatory columns (`name`, `location`, `rate` or `rating`, `cuisines` or `cuisines_list`) exist. Raise an explicit `SchemaError` with a helpful message if the upstream HF dataset schema has changed.

**Offline detection** (edgecase.md §1):
- If no cached file exists and the HF download fails with a connection error, catch the exception and raise a user-friendly `DatasetUnavailableError` instead of crashing with a raw traceback.

#### [NEW] [src/services/response_validator.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/response_validator.py)
**LLM response sanitization** (edgecase.md §5, §6):
- **Markdown fence stripping**: Detect and remove `` ```json ... ``` `` wrappers from raw LLM output before `json.loads()`.
- **Schema validation**: Validate that the parsed JSON contains the expected `recommendations` key (handle alternative keys like `recs`, `results`).
- **Anti-hallucination cross-reference** (edgecase.md §6): Accept a set of valid candidate IDs/names. For each recommendation returned by the LLM:
  1. Try exact `id` match against the candidate map.
  2. Fall back to case-insensitive exact `name` match.
  3. Fall back to fuzzy substring `name` match.
  4. Discard unmatched recommendations and log a warning.
- If **all** LLM recommendations are rejected as hallucinations, raise `HallucinationError` so the orchestrator can trigger fallback ranking.

#### [MODIFY] [llm_client.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/llm_client.py)
**API key validation** (edgecase.md §4):
- Before making the first API call, check if `groq_api_key` is empty or is a placeholder value (`"your-api-key-here"`, `"sk-..."` with length < 20). If so, raise a clear `ConfigurationError` immediately instead of letting the Groq SDK return a cryptic 401.

**Context window guard** (edgecase.md §4):
- Before sending the prompt, estimate the token count (rough heuristic: `len(prompt) / 4`). If it exceeds a configurable `MAX_PROMPT_TOKENS` threshold (default ~6000), log a warning and truncate the candidate list.

**Temperature reduction retry** (architecture.md §2.4):
- On the first JSON parse failure, retry once with `temperature=0.1` to improve output consistency before raising the error.

#### [MODIFY] [recommendation.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/recommendation.py)
**Integrate response_validator** (edgecase.md §6):
- Wire the new `response_validator` module into `_rank_with_llm()`. Replace the inline id/name matching logic with the validator's anti-hallucination cross-referencing.
- Catch `HallucinationError` and fall through to the fallback ranking.

**Token usage and latency logging** (architecture.md §8.3):
- Log the model name, latency (wall-clock time), and token usage (`prompt_tokens`, `completion_tokens`) from the Groq response after every LLM call.

#### [NEW] [src/services/errors.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/services/errors.py)
Centralized custom exception hierarchy:
- `ConfigurationError` — missing/invalid API key or settings.
- `DatasetUnavailableError` — HF download failed and no cache exists.
- `SchemaError` — upstream dataset schema changed.
- `HallucinationError` — LLM produced only invalid/hallucinated recommendations.
- `ValidationError` — user input validation failures (re-exported from `validator.py` for convenience).

#### [NEW] [src/logging_config.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/logging_config.py)
**Structured logging setup** (architecture.md §8.3):
- Configure Python's `logging` module with a consistent format: `[%(asctime)s] %(name)s %(levelname)s — %(message)s`.
- Set default level to `INFO`; allow override via `LOG_LEVEL` env var.
- Ensure all modules (`data.*`, `services.*`) use named loggers for granular control.
- **Security**: Never log the full `GROQ_API_KEY`; mask it to `gsk_…****` in startup logs.

#### [MODIFY] [config.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/config.py)
- Add `LOG_LEVEL` setting (default `"INFO"`).
- Add `MAX_PROMPT_TOKENS` setting (default `6000`).
- Add `GROQ_FALLBACK_MODEL` setting (default `"llama-3.1-8b-instant"`) from architecture.md §2.4.
- Add `FRONTEND_URL` setting (default `"http://localhost:3000"`) for CORS configuration.

#### [NEW] [tests/test_response_validator.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/tests/test_response_validator.py)
Unit tests covering:
- Markdown fence stripping from LLM responses.
- Schema validation (missing `recommendations` key, alternative key names).
- Anti-hallucination: valid IDs pass, invalid IDs are discarded, all-hallucinated triggers error.
- Fuzzy name matching edge cases.

#### [NEW] [tests/test_error_handling.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/tests/test_error_handling.py)
Integration tests covering:
- Corrupted Parquet cache triggers re-download.
- Missing API key raises `ConfigurationError` before any API call.
- Context window guard truncates oversized prompts.
- Temperature reduction retry on malformed JSON.

---

### Phase 6: FastAPI Backend API Layer
Expose the recommendation engine as a RESTful API consumed by the Next.js frontend. This replaces the direct Streamlit integration.

#### [NEW] [src/api/__init__.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/__init__.py)
Package init.

#### [NEW] [src/api/main.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/main.py)
FastAPI application factory with **lifespan** context manager:

**Startup (lifespan)**:
- Initialize `DatasetLoader` → load/cache the Parquet dataset.
- Initialize `DataPreprocessor` → clean and normalize.
- Initialize `RestaurantRepository` → hold processed data in memory.
- Store the repository instance in `app.state` for dependency injection.
- Log startup time and dataset size.

**App Configuration**:
- Title: `"AI Restaurant Recommender API"`.
- Version: `"1.0.0"`.
- Mount all route modules under `/api/v1` prefix.
- Global exception handlers mapping domain errors (`ConfigurationError`, `DatasetUnavailableError`, `ValidationError`) to appropriate HTTP status codes (500, 503, 422).

**CORS Middleware**:
- Allow origins: `[settings.FRONTEND_URL]` (default `http://localhost:3000`).
- Allow methods: `GET, POST, OPTIONS`.
- Allow headers: `Content-Type, Authorization`.
- Allow credentials: `true`.

#### [NEW] [src/api/schemas.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/schemas.py)
Pydantic V2 request/response models for the API layer:

```python
class RecommendRequest(BaseModel):
    location: str                        # required
    budget: Literal["low", "medium", "high"]
    cuisine: str | None = None           # optional
    min_rating: float = Field(ge=0.0, le=5.0, default=3.5)
    rest_type: str | None = None         # optional: Casual Dining, Café, etc.
    online_order: bool | None = None
    book_table: bool | None = None
    additional: str | None = None        # free-text preferences

class RecommendationItem(BaseModel):
    rank: int
    name: str
    cuisines: list[str]
    rating: float | None
    votes: int
    cost_for_two: int | None
    budget_tier: str
    rest_type: str | None
    online_order: bool
    book_table: bool
    explanation: str                     # LLM-generated

class FiltersMeta(BaseModel):
    applied: dict[str, Any]
    relaxed: list[str]                   # which filters were auto-relaxed

class RecommendResponse(BaseModel):
    summary: str | None
    recommendations: list[RecommendationItem]
    metadata: dict[str, Any]             # candidates_considered, model, latency
    filters: FiltersMeta

class LocationsResponse(BaseModel):
    locations: list[str]

class CuisinesResponse(BaseModel):
    cuisines: list[str]

class RestTypesResponse(BaseModel):
    rest_types: list[str]

class HealthResponse(BaseModel):
    status: str                          # "healthy" | "degraded"
    dataset_loaded: bool
    restaurant_count: int
    groq_api_configured: bool
```

#### [NEW] [src/api/dependencies.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/dependencies.py)
FastAPI dependency injection functions:
- `get_repository(request) -> RestaurantRepository`: Retrieves the repository from `request.app.state`.
- `get_recommendation_service(repo) -> RecommendationService`: Constructs the orchestrator with its dependencies (filter, prompt builder, LLM client).
- `get_settings() -> Settings`: Returns the validated settings singleton.

#### [NEW] [src/api/routes/__init__.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/routes/__init__.py)
Package init registering routers.

#### [NEW] [src/api/routes/recommend.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/routes/recommend.py)
**`POST /api/v1/recommend`**:
- Accepts `RecommendRequest` body.
- Validates preferences using `src/services/validator.py`.
- Calls `RecommendationService.get_recommendations()`.
- Returns `RecommendResponse` with full recommendation data, metadata, and filter info.
- Error handling:
  - `ValidationError` → 422 with structured error detail.
  - `ConfigurationError` → 503 with message about missing API key.
  - `DatasetUnavailableError` → 503 with retry-after hint.
  - Unhandled exceptions → 500 with generic error message.

#### [NEW] [src/api/routes/metadata.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/routes/metadata.py)
**`GET /api/v1/locations`**: Returns sorted list of unique locations from the repository.
**`GET /api/v1/cuisines`**: Returns sorted list of unique cuisines from the repository.
**`GET /api/v1/rest-types`**: Returns sorted list of unique restaurant types.

All responses are cached in-memory (the data is static once loaded).

#### [NEW] [src/api/routes/health.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/routes/health.py)
**`GET /api/v1/health`**: Returns `HealthResponse` with:
- Dataset loaded status.
- Restaurant count.
- Whether `GROQ_API_KEY` is configured (boolean, never exposes the key).

#### [NEW] [src/api/middleware.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/api/middleware.py)
- **CORS**: Configured from `settings.FRONTEND_URL`.
- **Request logging**: Log method, path, status code, and latency for each request.
- **Global error handler**: Catch unhandled exceptions and return structured JSON error responses.

#### [NEW] [tests/test_api.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/tests/test_api.py)
FastAPI endpoint tests using `httpx.AsyncClient` + `TestClient`:
- `POST /api/v1/recommend` with valid preferences → 200 with recommendations.
- `POST /api/v1/recommend` with invalid preferences → 422 with structured errors.
- `GET /api/v1/locations` → returns list of locations.
- `GET /api/v1/cuisines` → returns list of cuisines.
- `GET /api/v1/health` → returns health status.
- CORS headers present on responses.

#### [DELETE] [src/ui/streamlit_app.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/ui/streamlit_app.py)
Remove the Streamlit frontend — replaced by the Next.js application.

#### [DELETE] [src/ui/\_\_init\_\_.py](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/src/ui/__init__.py)
Remove the UI package (Streamlit-specific).

---

### Phase 7: Premium Next.js Frontend
Build a **visually stunning, production-quality** Next.js web application. The UI should feel like a premium SaaS product — not a basic prototype.

#### [NEW] `frontend/` — Next.js Project Scaffold
Initialize using `npx -y create-next-app@latest ./` inside the `frontend/` directory with:
- TypeScript enabled.
- App Router (`src/app/`).
- ESLint enabled.
- No Tailwind (vanilla CSS for full design control).

#### [NEW] [frontend/src/app/globals.css](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/app/globals.css)
Centralized CSS design system. All styles live here.

**Design System Tokens**:
- **Color palette**: Deep indigo-to-violet gradient background (`#0f0c29 → #302b63 → #24243e`), indigo accent (`#6366f1`), violet highlight (`#8b5cf6`), warm amber for ratings (`#f59e0b`), emerald for success states (`#10b981`), rose for warnings (`#f43f5e`).
- **Typography**: Google Font **Inter** (body), **Outfit** (headings) — imported via `next/font/google`.
- **Spacing scale**: 4px base grid (0.25rem increments).
- **Border radius**: `8px` (buttons), `16px` (cards), `24px` (modals/hero).
- **Shadows**: Layered box-shadows with colored tints (e.g., `0 8px 32px rgba(99,102,241,0.25)`).

**Core CSS Components**:
1. **Animated gradient background**: Slow-moving gradient using `@keyframes gradient-shift` with `background-size: 400% 400%`.
2. **Glassmorphic cards**: `backdrop-filter: blur(16px)`, semi-transparent borders, hover lift + glow animation.
3. **Rank badge**: Pill-shaped gradient badges (#1 gold gradient, #2 silver, #3 bronze, rest indigo).
4. **Rating stars**: CSS-only star display using filled/empty star glyphs with amber color.
5. **Cost indicator**: Visual rupee indicator with proportional fill bars.
6. **Tag chips**: Rounded pill tags for cuisines, filters, restaurant types with subtle background tints.
7. **Skeleton loading cards**: Animated shimmer placeholders (pulsing gradient) shown while API responds.
8. **Staggered card entrance**: `@keyframes fadeSlideUp` with increasing `animation-delay` per card (`0.1s × index`).
9. **Filter summary bar**: Horizontal bar above results showing applied/relaxed filters with colored chips.
10. **Empty state hero**: Centered illustration area with a call-to-action when no search has been made.
11. **Error/warning banners**: Styled alert bars for API failures, no results, relaxed filters.
12. **Scrollbar styling**: Custom thin scrollbar matching the dark theme.
13. **Responsive breakpoints**: Cards stack vertically on narrow viewports; sidebar collapses to top on mobile.

#### [NEW] [frontend/src/app/layout.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/app/layout.tsx)
Root layout:
- Import and configure Google Fonts (`Inter`, `Outfit`) via `next/font/google`.
- Set `<html>` className with font variables.
- SEO metadata: title `"AI Restaurant Recommender"`, description, OpenGraph tags.
- Import `globals.css`.

#### [NEW] [frontend/src/app/page.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/app/page.tsx)
Home page — the single-page application:
- `'use client'` — client component for interactivity.
- Uses the `useRecommendations` hook for API state management.
- Fetches metadata (locations, cuisines, rest types) on mount from FastAPI.
- Conditionally renders: `HeroSection` (before search) → `SkeletonCards` (loading) → `ResultsGrid` (results) / `EmptyState` (no results) / `ErrorBanner` (errors).
- Layout: Sidebar (preferences) + Main area (results) on desktop; stacked on mobile.

#### [NEW] [frontend/src/types/index.ts](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/types/index.ts)
TypeScript interfaces mirroring the FastAPI Pydantic schemas:
- `RecommendRequest`, `RecommendResponse`, `RecommendationItem`, `FiltersMeta`.
- `LocationsResponse`, `CuisinesResponse`, `RestTypesResponse`, `HealthResponse`.

#### [NEW] [frontend/src/lib/api.ts](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/lib/api.ts)
API client module:
- `API_BASE_URL` from environment variable `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- `fetchRecommendations(prefs: RecommendRequest): Promise<RecommendResponse>` — POST to `/api/v1/recommend`.
- `fetchLocations(): Promise<string[]>` — GET `/api/v1/locations`.
- `fetchCuisines(): Promise<string[]>` — GET `/api/v1/cuisines`.
- `fetchRestTypes(): Promise<string[]>` — GET `/api/v1/rest-types`.
- `fetchHealth(): Promise<HealthResponse>` — GET `/api/v1/health`.
- All functions include error handling with typed error responses.

#### [NEW] [frontend/src/hooks/useRecommendations.ts](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/hooks/useRecommendations.ts)
Custom React hook managing the recommendation flow:
- State: `{ data, isLoading, error, hasSearched }`.
- `search(prefs)` — calls `fetchRecommendations`, manages loading/error transitions.
- `reset()` — clears results and returns to hero state.
- Aborts in-flight requests on new submissions using `AbortController`.

#### [NEW] [frontend/src/components/HeroSection.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/HeroSection.tsx)
Shown before first search:
- Large animated title with gradient text effect: "Discover Your Perfect Meal".
- Subtitle: "AI-powered restaurant recommendations tailored to your taste".
- Floating food emoji animation in the background (CSS only).
- Arrow indicator pointing to the sidebar.

#### [NEW] [frontend/src/components/PreferencePanel.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/PreferencePanel.tsx)
Sidebar preference form:
- Custom-styled header with icon: "🔍 Your Preferences".
- **Location**: Searchable `<select>` with all unique locations (fetched from API).
- **Budget**: Visual toggle buttons (Low / Medium / High) using CSS-styled radio buttons with active highlight.
- **Minimum Rating**: Range slider with star emoji label, value displayed as `"⭐ 4.0+"`.
- **Cuisine**: `<select>` with "Any" as default, alphabetically sorted (fetched from API).
- **Restaurant Type**: Optional `<select>` (Casual Dining, Quick Bites, Café, etc.) fetched from API.
- **Online Order / Book Table**: Two checkbox toggles with icons.
- **Additional Preferences**: Text input with placeholder `"e.g., family-friendly, outdoor seating…"`.
- **Submit button**: Full-width gradient button with hover animation: "✨ Get Recommendations".
- Footer: "Powered by Groq • llama-3.3-70b-versatile".

#### [NEW] [frontend/src/components/SkeletonCards.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/SkeletonCards.tsx)
Loading state:
- Display 3–5 skeleton shimmer cards (animated CSS placeholders).
- Overlay message: "🤖 AI is analyzing restaurants for you…" with a subtle CSS spinner.

#### [NEW] [frontend/src/components/FilterSummary.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/FilterSummary.tsx)
Filter metadata bar:
- Horizontal row of tag chips showing applied filters (green) and relaxed filters (amber with strikethrough).
- Renders from `RecommendResponse.filters`.

#### [NEW] [frontend/src/components/RecommendationCard.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/RecommendationCard.tsx)
Individual result card:
- **Rank badge**: Top-left corner pill — #1 gold gradient, #2 silver, #3 bronze, rest indigo.
- **Restaurant name**: Large heading with subtle text glow on hover.
- **Cuisine tags**: Row of small rounded chips (one per cuisine).
- **Rating display**: Star icon + numeric value + vote count in a compact row.
- **Cost display**: Rupee icon + formatted cost ("₹800 for two") with budget tier label chip.
- **Service flags**: Small icons for 🟢 Online Order / 📖 Book Table (if available).
- **AI explanation**: Italicized paragraph in a slightly inset area with a subtle left border accent.
- **Hover effect**: Card lifts (`translateY(-6px)`) with an indigo glow shadow.
- **Entrance animation**: Cards fade-slide-up with staggered delay (0.1s per card index via `style={{ animationDelay }}`).

#### [NEW] [frontend/src/components/ResultsGrid.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/ResultsGrid.tsx)
Results container:
- **Summary banner**: LLM-generated summary in a highlighted glassmorphic container with a quote icon.
- **FilterSummary** component.
- Maps over `recommendations` array rendering `RecommendationCard` components.
- Responsive CSS grid layout (1 column mobile, 2 columns tablet, 3 columns desktop).

#### [NEW] [frontend/src/components/EmptyState.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/EmptyState.tsx)
No results state:
- Centered with "🍽️ No Matches Found" heading.
- Explanation text and filter relaxation suggestions.
- "Try Again" button linking back to the preference panel.

#### [NEW] [frontend/src/components/ErrorBanner.tsx](file:///Users/ris/Cursor/Restaurent%20Recommendation%20system/frontend/src/components/ErrorBanner.tsx)
Error display:
- **API error**: Amber warning banner: "AI explanation unavailable — showing results ranked by rating".
- **Network error**: Red banner with retry button.
- **Relaxed filters notice**: Info banner listing which constraints were loosened.
- Dismissible with a close button.

---

## Verification Plan

### Automated Tests
Implement unit tests in the `tests/` directory:
- Run using `pytest tests/`
  - `tests/test_filter.py`: Verify cascading filtering, ranking, and constraint relaxation.
  - `tests/test_preprocessor.py`: Verify rating and cost parsing with budget tier classifications.
  - `tests/test_recommendation.py`: Verify prompt building, mock LLM execution, response parsing, and fallback ranking.
  - `tests/test_response_validator.py`: Verify markdown stripping, schema validation, anti-hallucination cross-referencing.
  - `tests/test_error_handling.py`: Verify corrupted cache recovery, missing API key detection, context window guard, temperature retry.
  - `tests/test_api.py`: Verify FastAPI endpoints with `httpx.AsyncClient` — request validation, response schemas, error codes, CORS headers.

### Manual Verification
1. **Start the FastAPI backend**: `uvicorn src.api.main:app --reload --port 8000`.
2. **Start the Next.js frontend**: `cd frontend && npm run dev` (runs on port 3000).
3. **Test API directly**: Use `curl` or the auto-generated Swagger UI at `http://localhost:8000/docs`:
   - `POST /api/v1/recommend` with `{"location": "Banashankari", "budget": "medium", "cuisine": "North Indian", "min_rating": 4.0}`.
   - `GET /api/v1/locations` — verify dropdown data.
   - `GET /api/v1/health` — verify system status.
4. **Test the frontend**:
   - Open `http://localhost:3000`.
   - Verify hero section renders with animated gradient background.
   - Select location "Banashankari", budget "Medium", cuisine "North Indian", rating 4.0.
   - Submit and verify recommendations are fetched and render with premium glassmorphic cards with staggered animations.
   - Verify skeleton loading cards appear while the API responds.
   - Test edge cases (no matches found, API errors triggering fallback banners).
   - Verify filter relaxation banners when constraints are auto-relaxed.
   - Verify responsive layout: cards stack on mobile, sidebar collapses.
5. **Verify error states**:
   - Stop the FastAPI server → frontend shows network error banner with retry button.
   - Remove `GROQ_API_KEY` → health endpoint reports `groq_api_configured: false`, recommendations return fallback ranking with warning.
