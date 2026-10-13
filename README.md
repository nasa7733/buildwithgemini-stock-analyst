# MarketPulse

MarketPulse is an autonomous AI financial research and portfolio assistant built on the Google Agent Development Kit (ADK) and deployed via the Agent-to-Agent (A2A) protocol. It provides real-time equity research, macro rate tracking, database-backed portfolio watchlists, sandboxed financial computations, and multimodal media generation.

![MarketPulse Demo](demo.gif)

---

## What the Agent Does

MarketPulse is configured as an ADK ReAct reasoning agent using **`gemini-3.8-flash`** with integrated Google Cloud Platform services:

### 1. Firestore Portfolio Watchlist Backend
* **Database**: Google Cloud Firestore collection (`stocks`).
* **Tools**:
  * `list_stocks(sector: str = "")`: Retrieves tracked equities, prices, sectors, P/E ratios, and research notes, with optional sector filtering.
  * `get_stock_details(ticker: str)`: Fetches full fundamentals, market capitalization, 52-week ranges, and investment theses.
  * `upsert_stock(...)`: Dynamically creates or updates stock records and valuation notes in Firestore.

### 2. Live Market & Macro Data Integration
* `fetch_live_stock_quote(ticker: str)`: Fetches real-time equity pricing, day price deltas, percentage changes, exchange metadata, and previous close prices.
* `fetch_treasury_rates(limit: int = 5)`: Fetches latest average US Treasury interest rates and benchmark yields directly from the US Department of the Treasury Fiscal Data API.

### 3. Agent Engine Code Execution Sandbox
* **Runtime**: Google Cloud Vertex AI Agent Engine Code Executor (`AgentEngineSandboxCodeExecutor`).
* **Capability**: Allows the agent to safely execute Python in an isolated remote sandbox environment to calculate Discounted Cash Flow (DCF) models, portfolio risk metrics, statistical regressions, and options formulas.

### 4. Multimodal Generation & Public Cloud Storage
* **Visual Infographics**:
  * `generate_market_visual`: Uses **`gemini-3.1-flash-lite-image`** in the `global` location to generate market sentiment graphics and technical charts.
  * Saves images to ADK session artifacts (`tool_context.save_artifact`) and streams raw bytes directly to a public Google Cloud Storage bucket (`market-pulse-media-*`).
* **Motion Graphics & Video**:
  * `generate_market_video`: Uses Google's Omni model (**`gemini-omni-flash-preview`**) in the `global` location via the Google Interactions API to produce short motion graphics and chart animations.
  * Saves videos as session artifacts and uploads directly to the public Cloud Storage bucket.

### 5. Chat UI & A2UI Renderer
* **FastAPI Proxy**: Translates browser requests to the deployed agent over the A2A protocol using Google Application Default Credentials (ADC).
* **Frontend**: Lightweight chat interface with native rendering support for both text and A2UI cards.

*(Note: Cross-session Memory Bank long-term preference persistence is planned, not yet implemented).*

---

## Architecture Overview

```
Browser Chat UI (HTML / JS / CSS)
       │
       ▼  HTTP /chat
FastAPI Proxy (A2A Client + ADC Auth)
       │
       ▼  A2A Protocol (Agent Runtime / Reasoning Engine)
MarketPulse Root Agent (ADK + gemini-3.8-flash)
       ├── Firestore (Watchlist & Fundamentals DB)
       ├── Vertex AI Sandbox (Python Code Execution)
       ├── Vertex AI GenAI (gemini-3.1-flash-lite-image)
       ├── Vertex AI Interactions (gemini-omni-flash-preview)
       ├── Public Cloud Storage (Public Media Bucket)
       └── External APIs (US Treasury Fiscal Data & Market Quotes)
```

---

## Local Setup & Run

### Prerequisites
* Python 3.10+
* `uv` or `pip`
* Google Cloud SDK (`gcloud`) with access to your GCP project

### 1. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <your-project-id>
```

### 2. Install Project Dependencies
From the repository root:
```bash
uv pip install -r requirements.txt
# or: agents-cli install
```

### 3. Run the Agent Playground
To interact with the agent in the ADK development playground:
```bash
agents-cli playground
```

### 4. Run the Web Frontend & A2A Proxy Locally
Navigate to the `frontend/` directory, set the deployed agent target variables, and start the proxy server:
```bash
cd frontend
pip install -r requirements.txt

export AGENT_ENGINE_RESOURCE_NAME="projects/<project-id>/locations/<region>/reasoningEngines/<engine-id>"
export AGENT_DIRECTORY="app"

python main.py
```
Open a browser to port `8080` to access the chat interface.

---

## Running Tests

Run the test suite using pytest:
```bash
pytest tests/unit
```
