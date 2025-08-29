# zorever-assessment

AI-powered Real Estate FAQ Chatbot for Zorever. Answers FAQs, fetches property details from CSV, and captures visit bookings into a CSV. Includes a Streamlit UI with filters, sorting, and image cards.

> Assessment window: Start 26 Aug 2025 (00:00 IST) — End 29 Aug 2025 (23:59 IST)

## Repo Structure

```
zorever-assessment/
├─ data/
│  ├─ properties.csv        # provided dataset (used by the bot)
│  └─ visits.csv            # created/append-on-booking (generated at runtime)
├─ src/
│  ├─ app.py                # Streamlit UI and chat logic
│  └─ helpers.py            # data loading, lookup, FAQs, booking persistence
├─ tests/
│  └─ test_basic.py         # (optional) basic unit test
├─ requirements.txt
└─ README.md
```

## Quickstart (Python 3.10+)

```bash
python -m venv venv
source venv/bin/activate          # mac/linux
# venv\Scripts\activate         # windows
pip install -r requirements.txt

# run the UI
streamlit run src/app.py
```

Put the provided dataset at `data/properties.csv` before running. The app creates/appends `data/visits.csv` on booking.

## Features

- **Chatbot**
  - Generic FAQs: office location, working hours
  - Property lookup by `listing_id` (e.g., `P003`) or property name (case-insensitive substring)
  - Returns concise details (name, city, area_sqft, bedrooms, bathrooms, price, availability, short description, contact)
- **Booking automation**
  - Trigger: say "book a visit", "schedule visit", etc.
  - Flow: asks for name → phone → optional property id/name
  - Persists to `data/visits.csv` with columns:
    - `timestamp` (UTC ISO), `listing_id`, `property_name`, `name`, `phone`, `user_message`
  - Creates the CSV with header if missing
- **Property grid UI**
  - Search: keyword search by property name
  - Filters: City, Type, Price range
  - Sorting: Price (asc/desc), Area (high→low), Bedrooms (high→low)
  - Clear filters button
  - Image cards with details and quick "Select for booking" action

## Optional: LLM Polish

To enable LLM polish for more natural replies:

1. Get a free API key from [OpenRouter](https://openrouter.ai/)
2. Set environment variable:
   ```bash
   export LLM_API_KEY=your_key_here  # mac/linux
   set LLM_API_KEY=your_key_here     # windows
   ```
3. Restart the app - property replies will be automatically polished

The LLM only rewrites CSV-derived facts, preventing hallucinations.

## Demo Script (3-minute video)

### 1. FAQ Test (30 seconds)
- Type: "Where is your office?"
- Expected: "Our head office is at 123 Palm St, Dubai."

### 2. Property Lookup (45 seconds)
- Type: "What is the price of P003?"
- Expected: Details for Marina Studio with price $95,000 USD
- Type: "Show details for Sunrise Apartments"
- Expected: Property details with LLM polish (if API key set)

### 3. Property Grid (45 seconds)
- Click "Show all properties"
- Demonstrate filters: select "Dubai" city, adjust price range
- Show sorting: change to "Price (high→low)"
- Use search: type "Villa" to filter
- Click "Clear All Filters"

### 4. Booking Flow (60 seconds)
- Type: "I want to book a visit"
- Enter name: "John Doe"
- Enter phone: "1234567890"
- Enter property: "P003" (or type "skip")
- Show success message
- Navigate to "View All Bookings" section
- Show `data/visits.csv` contains the new booking

## How to Demo

1) Ask an FAQ: "Where is your office?"
2) Property details: "What is the price of P003?" or "Show details for Sunrise Apartments"
3) Booking: "I want to book a visit" → provide name, phone, and property (or type `skip`) → verify `data/visits.csv` is updated

## Notes

- Keep `data/properties.csv` unchanged (you may derive fields in code, but don't modify the file).
- Don't submit `data/visits.csv` with real phone numbers.
- Grant repo access to `zorever20x@gmail.com` when submitting.

## License

For assessment use only.
