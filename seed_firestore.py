# Copyright 2026 Google LLC
"""Seed script for MarketPulse Firestore watchlist / portfolio collections."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-fd61023443e8"

SEEDED_STOCKS = [
    {
        "ticker": "GOOGL",
        "company_name": "Alphabet Inc.",
        "sector": "Technology",
        "price": 182.50,
        "change_percent": 1.45,
        "market_cap_b": 2280.0,
        "pe_ratio": 24.8,
        "high_52w": 191.75,
        "low_52w": 131.25,
        "notes": "Strong cloud revenue and enterprise AI adoption.",
    },
    {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "price": 234.20,
        "change_percent": -0.32,
        "market_cap_b": 3580.0,
        "pe_ratio": 34.2,
        "high_52w": 237.23,
        "low_52w": 164.08,
        "notes": "Services growth offset by slight hardware replacement cycle delays.",
    },
    {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "sector": "Semiconductors",
        "price": 138.80,
        "change_percent": 2.80,
        "market_cap_b": 3410.0,
        "pe_ratio": 58.4,
        "high_52w": 140.76,
        "low_52w": 39.23,
        "notes": "Data center accelerator demand remains robust.",
    },
    {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "price": 428.15,
        "change_percent": 0.85,
        "market_cap_b": 3180.0,
        "pe_ratio": 35.1,
        "high_52w": 468.35,
        "low_52w": 320.10,
        "notes": "Azure cloud expansion and enterprise Copilot seat growth.",
    },
    {
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "sector": "Automotive / Clean Energy",
        "price": 218.40,
        "change_percent": -1.15,
        "market_cap_b": 695.0,
        "pe_ratio": 62.3,
        "high_52w": 271.00,
        "low_52w": 138.80,
        "notes": "Energy storage division growing rapidly; FSD software evaluation.",
    },
]


def seed():
    print(f"Connecting to Firestore for project {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("stocks")

    for item in SEEDED_STOCKS:
        doc_ref = collection.document(item["ticker"])
        doc_ref.set(item)
        print(f"Seeded stock: {item['ticker']} - {item['company_name']}")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
