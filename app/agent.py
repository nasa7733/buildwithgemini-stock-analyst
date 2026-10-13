# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from typing import Any
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google import genai
from google.cloud import firestore, storage
from google.genai import types


MODEL = "gemini-3.8-flash"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
OMNI_VIDEO_MODEL = "gemini-omni-flash-preview"
PROJECT_ID = "qwiklabs-gcp-04-fd61023443e8"
BUCKET_NAME = "market-pulse-media-qwiklabs-gcp-04-fd61023443e8"



def get_firestore_client() -> firestore.Client:
    """Return a Firestore client using the hardcoded GCP project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_stocks(sector: str = "") -> list[dict[str, Any]]:
    """List stocks from the Firestore watchlist/catalog, optionally filtered by sector.

    Args:
        sector: Optional sector filter (e.g. 'Technology', 'Semiconductors'). If empty, returns all stocks.

    Returns:
        A list of stock dictionary records with ticker, price, sector, P/E ratio, and notes.
    """
    db = get_firestore_client()
    collection = db.collection("stocks")

    if sector:
        docs = collection.where("sector", "==", sector).stream()
    else:
        docs = collection.stream()

    results = []
    for doc in docs:
        results.append(doc.to_dict())
    return results


def get_stock_details(ticker: str) -> dict[str, Any]:
    """Get detailed financial metrics and notes for a specific stock ticker.

    Args:
        ticker: The stock symbol (e.g. 'GOOGL', 'AAPL', 'NVDA').

    Returns:
        A dictionary with stock price, 52-week high/low, P/E ratio, market cap, and notes,
        or an error message if not found.
    """
    db = get_firestore_client()
    doc_ref = db.collection("stocks").document(ticker.upper())
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Stock ticker {ticker.upper()} not found in watchlist."}
    return doc.to_dict()


def upsert_stock(
    ticker: str,
    company_name: str,
    sector: str,
    price: float,
    notes: str = "",
    pe_ratio: float = 0.0,
    market_cap_b: float = 0.0,
) -> dict[str, Any]:
    """Add or update a stock in the Firestore portfolio/watchlist.

    Args:
        ticker: Stock ticker symbol (e.g. 'AMZN').
        company_name: Full name of the company.
        sector: Industry sector (e.g. 'E-Commerce / Cloud').
        price: Current share price.
        notes: Investment thesis or notes.
        pe_ratio: Price-to-earnings ratio.
        market_cap_b: Market cap in billions.

    Returns:
        Status dictionary confirming the stock was saved.
    """
    db = get_firestore_client()
    doc_ref = db.collection("stocks").document(ticker.upper())

    data = {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "sector": sector,
        "price": price,
        "notes": notes,
        "pe_ratio": pe_ratio,
        "market_cap_b": market_cap_b,
        "updated_at": datetime.datetime.now(ZoneInfo("UTC")).isoformat(),
    }
    doc_ref.set(data, merge=True)
    return {"status": "success", "message": f"Saved {ticker.upper()} ({company_name}) to watchlist."}


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a market or city.

    Args:
        query: The name of the city or market center (e.g. 'New York', 'San Francisco').

    Returns:
        A string with current time information.
    """
    q = query.lower()
    if "ny" in q or "new york" in q:
        tz_identifier = "America/New_York"
    elif "sf" in q or "san francisco" in q:
        tz_identifier = "America/Los_Angeles"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"

def fetch_live_stock_quote(ticker: str) -> dict[str, Any]:
    """Fetch real-time stock market quote and day statistics for a ticker.

    Args:
        ticker: The stock symbol (e.g. 'NVDA', 'AAPL', 'MSFT', 'GOOGL').

    Returns:
        A dictionary with live market price, previous close, day's change, currency, and timestamp.
    """
    import json
    import urllib.request

    symbol = ticker.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            meta = data["chart"]["result"][0]["meta"]
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose", current_price)
            change = round(current_price - prev_close, 2) if current_price and prev_close else 0.0
            change_percent = round((change / prev_close) * 100, 2) if prev_close else 0.0

            return {
                "ticker": symbol,
                "current_price": current_price,
                "previous_close": prev_close,
                "day_change": change,
                "day_change_percent": change_percent,
                "currency": meta.get("currency", "USD"),
                "instrument_type": meta.get("instrumentType", "EQUITY"),
                "exchange_name": meta.get("exchangeName", ""),
            }
    except Exception as e:
        return {"error": f"Failed to fetch live quote for {symbol}: {str(e)}"}


def fetch_treasury_rates(limit: int = 5) -> dict[str, Any]:
    """Fetch recent US Treasury benchmark interest rates (e.g. Bills, Notes, Bonds) from the official US Fiscal Data public API.

    Args:
        limit: Maximum number of recent security rate records to return (default 5).

    Returns:
        A dictionary with the record date and list of treasury securities with their average interest rate amounts.
    """
    import json
    import urllib.request

    url = (
        f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
        f"?sort=-record_date&page[size]={limit}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "MarketPulse/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            records = []
            for item in data.get("data", []):
                records.append({
                    "record_date": item.get("record_date"),
                    "security_desc": item.get("security_desc"),
                    "security_type": item.get("security_type_desc"),
                    "avg_interest_rate": f"{item.get('avg_interest_rate_amt')}%",
                })
            return {"status": "success", "rates": records}
    except Exception as e:
        return {"error": f"Failed to fetch US Treasury benchmark rates: {str(e)}"}


async def generate_market_visual(
    prompt: str,
    item_name: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a market insight illustration, sentiment badge, or stock infographic using gemini-3.1-flash-lite-image.

    The generated image is saved as a session artifact and uploaded directly to the public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the visual to generate (e.g. 'Sleek neon bullish green upward chart for NVDA').
        item_name: Identifier or stock ticker for the visual (e.g. 'NVDA', 'tech-sector', 'market-sentiment').
        tool_context: ADK execution context provided automatically for saving artifacts.

    Returns:
        A dictionary containing the public Cloud Storage image URL, artifact filename, and status.
    """
    import re
    import uuid

    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", item_name.lower())
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{clean_name}_{unique_id}.jpg"

    try:
        genai_client = genai.Client(vertexai=True, location="global")
        response = genai_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
            ),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "Image model did not return image data."}

        # 1. Save artifact to ToolContext for the Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)


        # 2. Upload image bytes directly to the public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "artifact_filename": filename,
            "public_url": public_url,
            "message": f"Generated image for {item_name}. Public URL: {public_url}",
        }
    except Exception as e:
        return {"error": f"Failed to generate and store market visual: {str(e)}"}


async def generate_market_video(
    prompt: str,
    item_name: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a short market video or motion graphic using Google's Omni model (gemini-omni-flash-preview) in the global region.

    The generated video is saved as a session artifact and uploaded directly to the public Cloud Storage bucket.

    Args:
        prompt: Description of the video or motion graphic to generate (e.g. '3 second dynamic stock chart animation showing bullish breakout for AAPL').
        item_name: Stock ticker or topic identifier (e.g. 'AAPL', 'bull-market', 'tech-breakout').
        tool_context: ADK execution context provided automatically for saving artifacts.

    Returns:
        A dictionary containing the public Cloud Storage video URL, artifact filename, and status.
    """
    import base64
    import re
    import uuid
    import google.auth
    import google.auth.transport.requests
    import requests

    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", item_name.lower())
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{clean_name}_{unique_id}.mp4"

    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())

        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "model": OMNI_VIDEO_MODEL,
            "input": [
                {"type": "text", "text": prompt}
            ],
            "response_format": [
                {
                    "type": "video",
                    "aspect_ratio": "16:9",
                    "resolution": "720p",
                    "duration": "3s",
                }
            ],
            "generation_config": {
                "video_config": {"task": "text_to_video"}
            },
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()

        video_bytes = None
        mime_type = "video/mp4"

        for step in data.get("steps", []):
            if step.get("type") == "model_output":
                for item in step.get("content", []):
                    if item.get("type") == "video":
                        raw_data = item.get("data") or item.get("bytes")
                        if raw_data:
                            video_bytes = base64.b64decode(raw_data)
                            mime_type = item.get("mime_type") or "video/mp4"
                            break
            if video_bytes:
                break

        if not video_bytes:
            return {"error": "Omni video model did not return video bytes in interaction response."}

        # 1. Save artifact to ToolContext for the Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to the public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "artifact_filename": filename,
            "public_url": public_url,
            "message": f"Generated short video for {item_name}. Public URL: {public_url}",
        }
    except Exception as e:
        return {"error": f"Failed to generate and store market video: {str(e)}"}


# Agent Engine Code Execution Sandbox
SANDBOX_RESOURCE_NAME = (
    "projects/11158291279/locations/us-east1/reasoningEngines/2902760175351889920/sandboxEnvironments/3981929738502406144"
)
code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are MarketPulse (STOCK ANALYST), an intelligent financial research and portfolio assistant. "
        "You help users monitor stock watchlists, evaluate company fundamentals, check live prices, "
        "inspect macro US Treasury benchmark rates, and generate visual infographics or videos. "
        "When presenting stock watchlists or catalog tables: DO NOT include a 'Notes' column or arbitrary disclaimers. "
        "Instead, provide a concise 'Market Sentiment' section highlighting momentum, market drivers, and bullish/bearish indicators. "
        "You can safely run Python code calculations, financial formulas, statistical simulations, or data analysis "
        "in your Agent Engine sandbox code execution environment. "
        "Use the provided tools to list stocks, fetch details, fetch live quotes, fetch treasury rates, "
        "generate market visuals, generate market videos, or add/update stocks when requested."
    ),
    code_executor=code_executor,
    tools=[
        list_stocks,
        get_stock_details,
        upsert_stock,
        fetch_live_stock_quote,
        fetch_treasury_rates,
        generate_market_visual,
        generate_market_video,
        get_current_time,
    ],
)



app = App(
    root_agent=root_agent,
    name="app",
)


