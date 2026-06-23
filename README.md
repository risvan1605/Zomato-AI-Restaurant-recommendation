# 🍽️ Restaurant Recommendation System

AI-powered restaurant recommendation engine built on the Zomato dataset. Uses a **filter-first, reason-second** approach: deterministic filters narrow down candidates, then a Groq-hosted LLM ranks and explains the top picks.

## Project Structure

```
├── .env.example              # Environment variable template
├── .gitignore
├── requirements.txt          # Python dependencies
├── README.md
│
├── docs/                     # Project documentation
│   ├── architecture.md       # System architecture & data flow
│   ├── context.md            # Dataset context & analysis
│   ├── edgecase.md           # Edge case handling strategy
│   ├── implementation_plan.md# Phase-wise build plan
│   └── Problem Statement.txt # Original problem statement
│
├── src/                      # Application source code
│   ├── __init__.py
│   ├── config.py             # Centralized settings (pydantic-settings)
│   │
│   ├── models/               # Domain models (dataclasses)
│   │   ├── __init__.py
│   │   ├── restaurant.py     # Restaurant schema
│   │   ├── preferences.py    # UserPreferences schema
│   │   └── recommendation.py # Recommendation & Response schemas
│   │
│   ├── data/                 # Data ingestion & preprocessing
│   │   ├── __init__.py
│   │   ├── loader.py         # HF dataset download + Parquet cache
│   │   ├── preprocessor.py   # Rating/cost parsing, budget tiers
│   │   └── repository.py     # Catalog queries & dropdown helpers
│   │
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── filter.py         # Cascading constraint filter engine
│   │   ├── prompt_builder.py # LLM prompt templates
│   │   ├── llm_client.py     # Groq SDK wrapper with retries
│   │   └── recommendation.py # Orchestrator (filter → LLM → response)
│   │
│   └── ui/                   # Presentation layer
│       ├── __init__.py
│       └── streamlit_app.py  # Streamlit frontend
│
└── tests/                    # Unit tests
    ├── __init__.py
    ├── test_filter.py
    ├── test_preprocessor.py
    └── test_recommendation.py
```

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# → Edit .env and set your GROQ_API_KEY

# 3. Run the app
streamlit run src/ui/streamlit_app.py

# 4. Run tests
pytest tests/
```

## Tech Stack

| Layer        | Technology                                |
| ------------ | ----------------------------------------- |
| Dataset      | Hugging Face `datasets` + Parquet cache   |
| Models       | Python dataclasses + Pydantic             |
| Config       | pydantic-settings + `.env`                |
| LLM          | Groq (`llama-3.3-70b-versatile`)          |
| Frontend     | Streamlit                                 |
| Tests        | pytest                                    |
