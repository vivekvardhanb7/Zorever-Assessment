import pandas as pd
import os
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import json

# File paths
PROPERTIES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "properties.csv")
BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "visits.csv")


def load_properties(path: Optional[str] = None) -> pd.DataFrame:
    """Load properties data from CSV. If path is provided, load from there."""
    csv_path = path if path is not None else PROPERTIES_FILE
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"{csv_path} not found.")


def save_booking(name: str, property_name: str, date) -> None:
    """Legacy simple booking saver used by form UI (kept for compatibility)."""
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    new_booking = pd.DataFrame([
        {"Name": name, "Property Name": property_name, "Date": str(date)}
    ])
    if os.path.exists(BOOKINGS_FILE):
        df_existing = pd.read_csv(BOOKINGS_FILE)
        df_updated = pd.concat([df_existing, new_booking], ignore_index=True)
    else:
        df_updated = new_booking
    df_updated.to_csv(BOOKINGS_FILE, index=False)


def save_visit_booking(
    listing_id: Optional[str],
    property_name: Optional[str],
    name: str,
    phone: str,
    user_message: str,
    out_path: Optional[str] = None,
) -> None:
    """Append a booking row with required columns to visits.csv.

    Columns: timestamp, listing_id, property_name, name, phone, user_message
    """
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    csv_path = out_path if out_path is not None else os.path.join(os.path.dirname(__file__), "..", "data", "visits.csv")
    row = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "listing_id": listing_id or "",
        "property_name": property_name or "",
        "name": name,
        "phone": phone,
        "user_message": user_message,
    }
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_updated = pd.concat([df_existing, pd.DataFrame([row])], ignore_index=True)
    else:
        df_updated = pd.DataFrame([row])
    df_updated.to_csv(csv_path, index=False)


def load_bookings():
    """Load all bookings."""
    if os.path.exists(BOOKINGS_FILE):
        return pd.read_csv(BOOKINGS_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Property Name", "Date"])


def find_property(df: pd.DataFrame, query: str) -> Optional[Dict[str, Any]]:
    """Find property by exact listing_id or case-insensitive substring of property_name."""
    if not query:
        return None
    q = str(query).strip()
    
    # exact listing match
    hit = df[df["listing_id"].str.upper() == q.upper()]
    if not hit.empty:
        return hit.iloc[0].to_dict()
    
    # name contains - more robust matching
    # Try exact match first
    hit = df[df["property_name"].str.lower() == q.lower()]
    if not hit.empty:
        return hit.iloc[0].to_dict()
    
    # Try contains match
    hit = df[df["property_name"].str.contains(q, case=False, na=False)]
    if not hit.empty:
        return hit.iloc[0].to_dict()
    
    # Try word-by-word matching for multi-word queries
    query_words = q.split()
    if len(query_words) > 1:
        for _, row in df.iterrows():
            property_name_lower = row["property_name"].lower()
            if all(word.lower() in property_name_lower for word in query_words):
                return row.to_dict()
    
    return None


FAQS = {
    "office": "Our head office is at 123 Palm St, Dubai.",
    "hours": "We are available 9am–6pm IST, Mon–Sat.",
}


def get_faq_answer(text: str) -> Optional[str]:
    t = (text or "").lower()
    if any(k in t for k in ["where is your office", "office location", "address"]):
        return FAQS["office"]
    if any(k in t for k in ["working hours", "hours", "timings"]):
        return FAQS["hours"]
    return None


def polish_with_llm(text: str, api_key: Optional[str] = None) -> str:
    """Optional LLM polish for replies. Returns original text if no API key."""
    if not api_key:
        return text
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "openrouter/auto",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful real estate assistant. Rewrite the following property information in a friendly, natural way. Keep all facts accurate and don't add information not present in the original text."
                },
                {
                    "role": "user",
                    "content": f"Please polish this property description: {text}"
                }
            ],
            "max_tokens": 200,
            "temperature": 0.3,
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return text
    except Exception:
        return text
