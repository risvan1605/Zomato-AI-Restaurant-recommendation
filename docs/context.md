# AI-Powered Restaurant Recommendation System — Project Context

> **Source:** Derived from `Problem Statement.txt`  
> **Last updated:** June 16, 2026  
> **Purpose:** This document captures the full project context, requirements, data model, workflow, and implementation guidance for building an AI-powered restaurant recommendation service inspired by Zomato.

---

## 1. Executive Summary

This project requires building an **AI-powered restaurant recommendation service** modeled after Zomato's discovery experience. The system combines:

- **Structured restaurant data** from a real-world Zomato dataset hosted on Hugging Face
- **User preference inputs** (location, budget, cuisine, ratings, and free-form preferences)
- **A Large Language Model (LLM)** to rank, explain, and optionally summarize recommendations in natural language

The end goal is a working application that filters relevant restaurants from the dataset, passes them to an LLM for intelligent ranking and explanation, and presents the top results in a clear, user-friendly format.

---

## 2. Problem Statement

**Build an AI-powered restaurant recommendation service inspired by Zomato.**

The system must intelligently suggest restaurants based on user preferences by **combining structured data with an LLM**. Recommendations should feel personalized and human-like—not merely a sorted list of database rows.

---

## 3. Core Objective

Design and implement an application that:

| # | Requirement | Description |
|---|-------------|-------------|
| 1 | **Accept user preferences** | Collect structured inputs such as location, budget, cuisine, minimum rating, and optional free-text preferences |
| 2 | **Use real-world data** | Load and work with the Zomato restaurant dataset from Hugging Face |
| 3 | **Leverage an LLM** | Generate personalized, human-like recommendations with reasoning |
| 4 | **Display useful results** | Present recommendations in a clear, actionable format for the end user |

---

## 4. System Workflow (End-to-End Pipeline)

The application follows a four-stage pipeline:

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Data Ingestion │ ──► │   User Input    │ ──► │  Integration Layer   │ ──► │ Recommendation  │
│  (Load & Prep)  │     │  (Preferences)  │     │  (Filter + Prompt)   │     │ Engine (LLM)    │
└─────────────────┘     └─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                                                      │
                                                                                      ▼
                                                                             ┌─────────────────┐
                                                                             │ Output Display  │
                                                                             │ (Top Results)   │
                                                                             └─────────────────┘
```

Each stage is described in detail below.

---

## 5. Stage 1: Data Ingestion

### 5.1 Data Source

- **Primary dataset:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on Hugging Face
- **Format:** CSV (also auto-converted to Parquet on Hugging Face)
- **Size:** ~51,717 restaurant records (~574 MB raw CSV)
- **Split:** Single `train` split under the `default` subset
- **Origin:** Based on Zomato Bangalore restaurant data (commonly sourced from Kaggle's Zomato Bangalore Restaurants dataset)

**Example loading code:**

```python
from datasets import load_dataset
import pandas as pd

dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
df = pd.DataFrame(dataset["train"])
```

> **Note:** A duplicate dataset exists at `dhavalpm/zomato-restaurant-recommendation` with identical schema and row count. Either can be used; the problem statement specifies the ManikaSaini source.

### 5.2 Preprocessing Requirements

Load the dataset and preprocess it for downstream filtering and LLM consumption. Key tasks include:

1. **Extract relevant fields** — Focus on fields needed for filtering, ranking, and display (see Section 6 for full schema)
2. **Clean ratings** — The `rate` column is stored as a string (e.g., `"4.1/5"`, `"NEW"`, `"-"`). Parse to numeric where possible; handle missing or invalid values
3. **Normalize cost** — `approx_cost(for two people)` is a string with varied formats; convert to numeric ranges or categories aligned with budget tiers (low / medium / high)
4. **Parse cuisines** — `cuisines` is a comma-separated string; split into individual cuisine tags for filtering
5. **Handle missing values** — Several text fields (e.g., `dish_liked`, `reviews_list`, `menu_item`) may be empty; decide which are required vs. optional for filtering
6. **Location normalization** — Map user-facing city names (e.g., "Delhi", "Bangalore") to dataset values in `location` and `listed_in(city)` columns

### 5.3 Dataset Schema (17 Fields)

| Field | Type | Cardinality / Range | Description | Relevance to Project |
|-------|------|---------------------|-------------|----------------------|
| `url` | string | 180–538 chars | Zomato URL for the restaurant listing | Optional link in output |
| `address` | string | 6–346 chars | Full street address | Context for LLM; display |
| `name` | string | 2–159 chars | Restaurant name | **Primary display field** |
| `online_order` | string | 2 values (Yes/No) | Whether online ordering is available | Filter for delivery preference |
| `book_table` | string | 2 values (Yes/No) | Whether table booking is available | Filter for dine-in planning |
| `rate` | string | 64 distinct values | Rating (typically `"X.X/5"`) | **Filter by minimum rating**; ranking signal |
| `votes` | int64 | 0–16,800 | Number of user votes/ratings | Popularity signal for ranking |
| `phone` | string | 11–34 chars (nullable) | Contact phone number | Optional display |
| `location` | string | 93 localities | Neighborhood/locality within city | **Filter by location** |
| `rest_type` | string | 93 types | Restaurant category (e.g., Casual Dining, Quick Bites) | Filter; LLM context |
| `dish_liked` | string | up to 134 chars (nullable) | Popular/liked dishes | LLM context for personalization |
| `cuisines` | string | 3–86 chars (nullable) | Comma-separated cuisine types | **Filter by cuisine** |
| `approx_cost(for two people)` | string | 70 distinct values | Estimated cost for two people (INR) | **Filter by budget** |
| `reviews_list` | string | up to ~1.28M chars | Raw review text blob | Rich context for LLM (use selectively due to size) |
| `menu_item` | string | up to ~24.9k chars | Menu items list | LLM context for food preferences |
| `listed_in(type)` | string | 7 categories | Listing category (e.g., Buffet, Cafes, Delivery) | Filter by dining type |
| `listed_in(city)` | string | 30 cities | City where restaurant is listed | **Filter by city/location** |

### 5.4 Fields Most Critical for the Application

Based on the problem statement, these fields drive the core user experience:

- **Filtering:** `location`, `listed_in(city)`, `cuisines`, `approx_cost(for two people)`, `rate`, `online_order`, `book_table`, `rest_type`, `listed_in(type)`
- **Display:** `name`, `cuisines`, `rate`, `approx_cost(for two people)`
- **LLM enrichment:** `dish_liked`, `reviews_list` (summarized), `menu_item`, `rest_type`, `votes`, `address`

---

## 6. Stage 2: User Input

Collect structured and semi-structured preferences from the user. The problem statement specifies the following inputs:

### 6.1 Required / Core Preferences

| Input | Type | Examples | Maps to Dataset |
|-------|------|----------|-----------------|
| **Location** | Categorical / text | Delhi, Bangalore, Banashankari | `location`, `listed_in(city)` |
| **Budget** | Categorical | low, medium, high | `approx_cost(for two people)` (mapped to cost ranges) |
| **Cuisine** | Categorical / multi-select | Italian, Chinese, North Indian | `cuisines` (substring / token match) |
| **Minimum rating** | Numeric / threshold | 3.5, 4.0, 4.5 | `rate` (parsed to float) |

### 6.2 Additional Preferences (Optional / Free-Form)

Users may provide extra preferences such as:

- **Family-friendly** — Could map to `rest_type`, review sentiment, or LLM inference
- **Quick service** — Could map to `rest_type` (e.g., Quick Bites, Food Truck) or `listed_in(type)` (Delivery)
- **Online ordering** — Maps directly to `online_order == "Yes"`
- **Table booking** — Maps directly to `book_table == "Yes"`
- **Any other natural-language preference** — Passed to the LLM prompt for reasoning

### 6.3 Budget Tier Mapping (Suggested)

The problem statement uses **low / medium / high** budget tiers. Since `approx_cost(for two people)` is stored as string values in INR, implement a mapping such as:

| Tier | Suggested INR Range (for two people) | Notes |
|------|--------------------------------------|-------|
| **Low** | ₹0 – ₹300 | Budget-friendly, street food, quick bites |
| **Medium** | ₹300 – ₹800 | Casual dining, mid-range |
| **High** | ₹800+ | Fine dining, premium experiences |

> Exact thresholds should be calibrated against the actual distribution of `approx_cost(for two people)` values in the dataset after preprocessing.

### 6.4 Input Collection UX Considerations

- Provide dropdowns or autocomplete for **location** and **cuisine** based on unique values in the dataset
- Use sliders or preset buttons for **minimum rating**
- Use radio buttons or segmented control for **budget**
- Include a free-text field for **additional preferences** to capture nuances the structured filters miss

---

## 7. Stage 3: Integration Layer

The integration layer sits between raw data filtering and the LLM. It is responsible for:

1. **Filtering** — Apply user preferences against the preprocessed dataset to produce a candidate set of restaurants
2. **Preparing structured context** — Format filtered results into a compact, LLM-friendly representation
3. **Prompt construction** — Design a prompt that enables the LLM to reason about and rank the candidates

### 7.1 Filtering Logic

Apply filters in a sensible order to reduce the candidate set before LLM processing:

```
ALL RESTAURANTS
    │
    ├─► Filter by location (city / locality)
    │
    ├─► Filter by cuisine (contains match)
    │
    ├─► Filter by budget tier (cost range)
    │
    ├─► Filter by minimum rating (rate >= threshold)
    │
    ├─► Apply optional filters (online_order, book_table, rest_type, etc.)
    │
    └─► CANDIDATE SET (top N rows, e.g., 20–50, for LLM input)
```

**Important constraints:**

- If the candidate set is too large, pre-truncate by rating/votes before sending to the LLM (token limit considerations)
- If the candidate set is empty after filtering, return a helpful message suggesting the user relax constraints
- Do not send the entire 51K-row dataset to the LLM—filter first

### 7.2 Structured Data for LLM Input

For each candidate restaurant, prepare a concise record containing:

```json
{
  "name": "Restaurant Name",
  "location": "Banashankari",
  "cuisines": "North Indian, Chinese",
  "rate": 4.2,
  "votes": 800,
  "approx_cost_for_two": 600,
  "rest_type": "Casual Dining",
  "dish_liked": "Paneer Butter Masala, Biryani",
  "online_order": "Yes",
  "book_table": "No"
}
```

Omit or truncate large fields (`reviews_list`, `menu_item`) unless specifically needed; if used, summarize or sample rather than passing full text.

### 7.3 Prompt Design Requirements

Design a prompt that instructs the LLM to:

1. **Understand user preferences** — Restate or acknowledge what the user asked for
2. **Evaluate each candidate** — Compare restaurants against stated preferences
3. **Rank options** — Order restaurants from best to worst fit
4. **Explain each recommendation** — Provide a human-like reason why each restaurant fits the user's needs
5. **Optionally summarize** — Offer a brief overview of the recommendation set (e.g., "Here are three great Italian spots in Bangalore under ₹800")

**Prompt structure (recommended):**

```
System: You are a restaurant recommendation assistant inspired by Zomato.
        Given user preferences and a list of candidate restaurants, rank
        the top recommendations and explain why each fits.

User Preferences:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional: {additional_preferences}

Candidate Restaurants:
{structured_restaurant_list}

Instructions:
- Return the top {N} recommendations ranked by best fit.
- For each restaurant, provide: name, cuisine, rating, estimated cost,
  and a 1–2 sentence explanation of why it matches the user's preferences.
- Optionally include a brief summary paragraph.
```

---

## 8. Stage 4: Recommendation Engine (LLM)

Use a Large Language Model as the core ranking and explanation engine.

### 8.1 LLM Responsibilities

| Task | Description |
|------|-------------|
| **Rank restaurants** | Order filtered candidates by best match to user preferences |
| **Provide explanations** | Generate natural-language reasons for each recommendation |
| **Summarize choices** | Optionally produce a high-level summary of the recommendation set |

### 8.2 LLM Selection Considerations

The problem statement does not mandate a specific LLM provider. Options include:

- OpenAI GPT models (GPT-4o, GPT-4o-mini)
- Anthropic Claude models
- Open-source models via Ollama, Hugging Face Inference API, etc.
- Google Gemini

Choose based on: cost, latency, explanation quality, and availability of API keys in the deployment environment.

### 8.3 Output Parsing

Define a structured output format from the LLM to simplify rendering:

- **Option A:** Request JSON output with ranked list and explanations
- **Option B:** Parse markdown-formatted response
- **Option C:** Use function calling / tool use for structured responses

Structured JSON is recommended for reliable UI rendering.

### 8.4 Guardrails

- Ensure the LLM only recommends restaurants from the provided candidate list (no hallucinated restaurants)
- Validate LLM output against the candidate set before display
- Handle LLM failures gracefully (fallback to rule-based ranking by rating/votes)

---

## 9. Stage 5: Output Display

Present the top recommendations in a **user-friendly format**. Each recommendation must include:

| Field | Source | Example |
|-------|--------|---------|
| **Restaurant Name** | `name` | "Jalsa" |
| **Cuisine** | `cuisines` | "North Indian, Mughlai" |
| **Rating** | `rate` (parsed) | 4.2 / 5 |
| **Estimated Cost** | `approx_cost(for two people)` | ₹800 for two |
| **AI-generated explanation** | LLM output | "Great fit for your medium budget and love of North Indian food, with consistently high ratings and popular biryani." |

### 9.1 Display Format Options

- **Web UI** — Cards or list view with rating stars, cost badge, and explanation text
- **CLI** — Formatted text output for terminal-based demos
- **API response** — JSON payload for programmatic consumption

### 9.2 Optional Enhancements (Not Required but Useful)

- Link to Zomato listing via `url`
- Show vote count as a popularity indicator
- Display `online_order` / `book_table` badges
- Show `dish_liked` highlights

---

## 10. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                              │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌─────────────┐ │
│  │  User Input │   │   Results    │   │  Web / CLI  │   │  API (opt)  │ │
│  │    Form     │──►│   Display    │◄──│    Shell    │   │  Endpoints  │ │
│  └──────┬──────┘   └──────▲───────┘   └─────────────┘   └─────────────┘ │
└─────────┼─────────────────┼──────────────────────────────────────────────┘
          │                 │
          ▼                 │
┌──────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATION LAYER                                │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────────────┐ │
│  │ Preference       │   │ Prompt Builder   │   │ Response Parser     │ │
│  │ Filter Engine    │──►│ (User prefs +    │──►│ (Structured output  │ │
│  │                  │   │  candidates)     │   │  validation)        │ │
│  └────────┬─────────┘   └────────┬─────────┘   └─────────────────────┘ │
└───────────┼──────────────────────┼───────────────────────────────────────┘
            │                      │
            ▼                      ▼
┌───────────────────────┐  ┌───────────────────────┐
│   DATA LAYER          │  │   LLM SERVICE         │
│  Hugging Face Dataset │  │  (OpenAI / Claude /   │
│  Preprocessing Pipeline│  │   local model, etc.)  │
└───────────────────────┘  └───────────────────────┘
```

---

## 11. Technology Stack (Suggested, Not Prescribed)

| Layer | Suggested Options |
|-------|-------------------|
| **Language** | Python 3.10+ |
| **Data loading** | `datasets`, `pandas` |
| **LLM integration** | `openai`, `anthropic`, `langchain`, or direct HTTP API calls |
| **UI** | Streamlit, Gradio, Flask/FastAPI + React, or CLI |
| **Environment** | `.env` for API keys; `requirements.txt` or `pyproject.toml` |

---

## 12. Success Criteria

The application is considered complete when it:

- [ ] Loads and preprocesses the Zomato dataset from Hugging Face
- [ ] Accepts user preferences (location, budget, cuisine, minimum rating, additional preferences)
- [ ] Filters the dataset based on user input
- [ ] Sends filtered candidates to an LLM with a well-designed prompt
- [ ] Receives ranked recommendations with explanations from the LLM
- [ ] Displays top results with: name, cuisine, rating, estimated cost, and AI explanation
- [ ] Handles edge cases (no results, invalid input, LLM errors)

---

## 13. Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| No restaurants match filters | Inform user; suggest broadening location, cuisine, or budget |
| Invalid location/cuisine | Validate against known dataset values; show autocomplete suggestions |
| Unparseable rating (`"NEW"`, `"-"`) | Exclude from rating filter or treat as unrated |
| LLM timeout or API error | Fall back to rule-based ranking (sort by rating, then votes) |
| Too many candidates for LLM context | Pre-rank by rating/votes and send top N (e.g., 20) |
| Empty optional fields | Skip gracefully; do not fail preprocessing |

---

## 14. Non-Functional Requirements (Implied)

- **Usability:** Results must be easy to scan and understand at a glance
- **Relevance:** Recommendations should clearly connect to stated user preferences in the explanation text
- **Performance:** Filtering should be near-instant; LLM call is the primary latency bottleneck
- **Maintainability:** Separate data loading, filtering, prompt building, LLM calls, and UI into distinct modules
- **Configurability:** LLM provider, model name, and API keys should be configurable via environment variables

---

## 15. Out of Scope (Not Mentioned in Problem Statement)

The following are **not** required unless explicitly added later:

- User accounts, login, or saved preferences
- Real-time Zomato API integration
- Geolocation / map-based search
- Payment or booking functionality
- Training a custom ML model (the LLM handles ranking/explanation; traditional ML is optional)
- Multi-city expansion beyond what exists in the dataset

---

## 16. Key References

| Resource | URL |
|----------|-----|
| Zomato dataset (primary) | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| Zomato dataset (duplicate) | https://huggingface.co/datasets/dhavalpm/zomato-restaurant-recommendation |
| Dataset viewer | https://huggingface.co/datasets/dhavalpm/zomato-restaurant-recommendation/viewer/default/train |
| Original Kaggle source (Bangalore) | https://www.kaggle.com/datasets/himanshupoddar/zomato-bangalore-restaurants |

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **LLM** | Large Language Model — used here for ranking, explanation, and summarization |
| **Candidate set** | Restaurants remaining after applying user preference filters, passed to the LLM |
| **Integration layer** | Middleware that filters data and constructs the LLM prompt |
| **Budget tier** | Categorical cost level: low, medium, or high |
| **Zomato** | Indian restaurant discovery and food delivery platform; inspiration for this project |

---

## 18. Open Implementation Decisions

These choices are left to the implementer:

1. **UI framework** — Streamlit vs. Gradio vs. custom web app vs. CLI
2. **LLM provider and model** — Based on cost, quality, and API access
3. **Number of recommendations** — Top 3, 5, or 10 (problem statement says "top recommendations" without a fixed count)
4. **Budget tier thresholds** — Exact INR ranges after analyzing cost distribution
5. **Whether to use review text** — Full `reviews_list` is very large; summarization or exclusion recommended
6. **Output format from LLM** — Free text vs. structured JSON

---

*This document should be treated as the single source of truth for project context. Update it as requirements evolve or implementation decisions are finalized.*
