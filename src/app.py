import os
import streamlit as st
import pandas as pd
from helpers import (
    load_properties,
    save_booking,
    load_bookings,
    find_property,
    get_faq_answer,
    save_visit_booking,
    polish_with_llm,
)

# ---------------- Chatbot Response Logic ---------------- #
def handle_message(user_text, df):
    """Process user input and return chatbot response with quick actions."""
    user_text = user_text.lower()

    if user_text in ["hi", "hello", "hey"]:
        return "Hello! 👋 How can I help you today?", ["Show all properties", "Book a visit", "FAQs", "Check amenities"]

    elif "properties" in user_text or "show all properties" in user_text:
        # Signal UI to render the property grid instead of long text
        st.session_state.show_properties = True
        return "Here are the available properties:", ["Book a visit", "Check amenities"]

    elif "book" in user_text or "visit" in user_text:
        st.session_state.booking_flow = {"step": "ask_name", "buffer": {}}
        return "Sure! Let's schedule a visit. Please share your full name:", []

    elif "amenities" in user_text:
        st.session_state.show_properties = False
        amenities = "\n".join([f"🏠 {row['property_name']}: {row['short_description']}" for _, row in df.iterrows()])
        return f"Here are the amenities for each property:\n\n{amenities}", []

    elif "faq" in user_text:
        return ("Here are some FAQs:\n\n"
                "1️⃣ Do you offer home loans? ✅ Yes, we have tie-ups with banks.\n"
                "2️⃣ Can I visit properties before booking? ✅ Yes, you can book a visit.\n"
                "3️⃣ Are there any hidden charges? ❌ No, all charges are transparent."), ["Show all properties", "Book a visit"]

    elif "price" in user_text:
        # Extract property ID/name from the question
        import re
        # Look for patterns like "P003", "P001", etc.
        prop_id_match = re.search(r'P\d+', user_text.upper())
        if prop_id_match:
            prop_id = prop_id_match.group()
            prop = find_property(df, prop_id)
            if prop:
                reply = (
                    f"{prop['property_name']} — {int(prop['bedrooms']) if prop['bedrooms'] else 0} BHK "
                    f"({int(prop['area_sqft'])} sqft) in {prop['city']}. Price: {int(prop['price']):,} {prop['price_currency']}. "
                    f"Status: {prop['availability']}.\nShort: {prop['short_description']}\nContact: {prop['agent_email']}"
                )
                # Optional LLM polish
                api_key = os.getenv("LLM_API_KEY")
                if api_key:
                    reply = polish_with_llm(reply, api_key)
                return reply, ["Book a visit", "Show all properties"]
        
        # Try general property lookup if no specific ID found
        prop = find_property(df, user_text)
        if prop:
            reply = (
                f"{prop['property_name']} — {int(prop['bedrooms']) if prop['bedrooms'] else 0} BHK "
                f"({int(prop['area_sqft'])} sqft) in {prop['city']}. Price: {int(prop['price']):,} {prop['price_currency']}. "
                f"Status: {prop['availability']}.\nShort: {prop['short_description']}\nContact: {prop['agent_email']}"
            )
            # Optional LLM polish
            api_key = os.getenv("LLM_API_KEY")
            if api_key:
                reply = polish_with_llm(reply, api_key)
            return reply, ["Book a visit", "Show all properties"]
        
        # If no specific property found, show all prices
        prices = "\n".join([
            f"{row['property_name']}: {int(row['price']):,} {row['price_currency']}" for _, row in df.iterrows()
        ])
        return f"Here are the property prices:\n\n{prices}", []

    else:
        # FAQ first
        faq = get_faq_answer(user_text)
        if faq:
            return faq, ["Show all properties", "Book a visit"]
        
        # Try property lookup with better text cleaning
        # First try exact match
        prop = find_property(df, user_text)
        if prop:
            reply = (
                f"{prop['property_name']} — {int(prop['bedrooms']) if prop['bedrooms'] else 0} BHK "
                f"({int(prop['area_sqft'])} sqft) in {prop['city']}. Price: {int(prop['price']):,} {prop['price_currency']}. "
                f"Status: {prop['availability']}.\nShort: {prop['short_description']}\nContact: {prop['agent_email']}"
            )
            # Optional LLM polish
            api_key = os.getenv("LLM_API_KEY")
            if api_key:
                reply = polish_with_llm(reply, api_key)
            return reply, ["Book a visit", "Show all properties"]
        
        # Try extracting property name from phrases like "Show details for Sunrise Apartments"
        import re
        # Remove common phrases and clean the text
        cleaned_text = user_text.lower()
        cleaned_text = re.sub(r'show details for|details for|information about|tell me about|what is|price of|property|apartment|villa|studio|office|house', '', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        if cleaned_text:
            prop = find_property(df, cleaned_text)
            if prop:
                reply = (
                    f"{prop['property_name']} — {int(prop['bedrooms']) if prop['bedrooms'] else 0} BHK "
                    f"({int(prop['area_sqft'])} sqft) in {prop['city']}. Price: {int(prop['price']):,} {prop['price_currency']}. "
                    f"Status: {prop['availability']}.\nShort: {prop['short_description']}\nContact: {prop['agent_email']}"
                )
                # Optional LLM polish
                api_key = os.getenv("LLM_API_KEY")
                if api_key:
                    reply = polish_with_llm(reply, api_key)
                return reply, ["Book a visit", "Show all properties"]
        
        return "I didn't understand that. Please try again.", ["Show all properties", "Book a visit"]

# ---------------- Streamlit App ---------------- #
def run_streamlit():
    st.set_page_config(page_title="Real Estate Chatbot", page_icon="🏡", layout="centered")

    st.title("🏡 Real Estate Chatbot")
    st.write("Welcome! How can I assist you today?")

    # Load property data
    df = load_properties()

    # Session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = [("assistant", "Hello! 👋 How can I help you today?")]
    if "dynamic_buttons" not in st.session_state:
        st.session_state.dynamic_buttons = ["Show all properties", "Book a visit", "FAQs", "Check amenities"]
    if "show_properties" not in st.session_state:
        st.session_state.show_properties = False
    if "selected_property_name" not in st.session_state:
        st.session_state.selected_property_name = None
    if "booking_flow" not in st.session_state:
        st.session_state.booking_flow = None
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "city": "All",
            "type": "All",
            "price": (0, 0),
            "sort_by": "Price (low→high)"
        }

    # Display chat history
    for role, msg in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(msg)

    # Quick Reply Buttons
    st.markdown("### 🔍 Quick Actions")
    num_buttons = len(st.session_state.dynamic_buttons)
    if num_buttons > 0:
        cols = st.columns(num_buttons)
        for i, btn in enumerate(st.session_state.dynamic_buttons):
            if cols[i].button(btn):
                st.session_state.messages.append(("user", btn))
                reply, dynamic_buttons = handle_message(btn, df)
                st.session_state.messages.append(("assistant", reply))
                st.session_state.dynamic_buttons = dynamic_buttons
                st.rerun()
    else:
        st.caption("No quick actions available.")

    # Chat input for user (with booking flow state machine)
    if user_text := st.chat_input("Type your question..."):
        st.session_state.messages.append(("user", user_text))
        # Booking flow handling
        if st.session_state.booking_flow:
            step = st.session_state.booking_flow.get("step")
            buf = st.session_state.booking_flow.get("buffer", {})
            if step == "ask_name":
                buf["name"] = user_text.strip()
                st.session_state.booking_flow = {"step": "ask_phone", "buffer": buf}
                reply, dynamic_buttons = ("Thanks! Please share your phone number:", [])
            elif step == "ask_phone":
                buf["phone"] = user_text.strip()
                st.session_state.booking_flow = {"step": "ask_property", "buffer": buf}
                reply, dynamic_buttons = ("Which property? You can send listing id like P003 or name (optional, type 'skip').", [])
            elif step == "ask_property":
                listing_id = None
                property_name = None
                if user_text.strip().lower() != "skip":
                    prop = find_property(df, user_text)
                    if prop:
                        listing_id = prop.get("listing_id")
                        property_name = prop.get("property_name")
                save_visit_booking(
                    listing_id=listing_id,
                    property_name=property_name,
                    name=buf.get("name", ""),
                    phone=buf.get("phone", ""),
                    user_message=user_text,
                )
                st.session_state.booking_flow = None
                reply, dynamic_buttons = ("✅ Booking captured. Our team will reach out shortly.", ["Show all properties"])
            else:
                st.session_state.booking_flow = None
                reply, dynamic_buttons = handle_message(user_text, df)
        else:
            reply, dynamic_buttons = handle_message(user_text, df)
        st.session_state.messages.append(("assistant", reply))
        st.session_state.dynamic_buttons = dynamic_buttons
        st.rerun()

    # ---------------- Property Grid ---------------- #
    st.markdown("---")
    if st.session_state.show_properties:
        st.subheader("🏠 Available Properties")

        def format_price(price, currency):
            symbol = "$" if currency == "USD" else ""
            try:
                price_num = float(price)
                price_str = f"{price_num:,.0f}"
            except Exception:
                price_str = str(price)
            return f"{symbol}{price_str} {currency}".strip()

        # Filters & Sorting
        with st.expander("Filters & Sorting", expanded=True):
            # Search bar
            search_term = st.text_input("🔍 Search properties by name", placeholder="e.g., Sunrise, Marina, Villa...")
            
            left, right = st.columns(2)
            with left:
                cities = ["All"] + sorted(df["city"].dropna().unique().tolist())
                selected_city = st.selectbox(
                    "City",
                    options=cities,
                    index=cities.index(st.session_state.filters.get("city", "All"))
                )
                types = ["All"] + sorted(df["property_type"].dropna().unique().tolist())
                selected_type = st.selectbox(
                    "Type",
                    options=types,
                    index=types.index(st.session_state.filters.get("type", "All"))
                )
            with right:
                min_price = int(df["price"].min())
                max_price = int(df["price"].max())
                current_min, current_max = st.session_state.filters.get("price", (min_price, max_price))
                if current_min == 0 and current_max == 0:
                    current_min, current_max = min_price, max_price
                selected_price = st.slider(
                    "Price range (USD)",
                    min_value=min_price,
                    max_value=max_price,
                    value=(current_min, current_max),
                    step=5000
                )
                sort_options = [
                    "Price (low→high)",
                    "Price (high→low)",
                    "Area (high→low)",
                    "Bedrooms (high→low)"
                ]
                selected_sort = st.selectbox(
                    "Sort by",
                    options=sort_options,
                    index=sort_options.index(st.session_state.filters.get("sort_by", "Price (low→high)"))
                )
            
            # Clear filters button
            if st.button("🗑️ Clear All Filters"):
                st.session_state.filters = {
                    "city": "All",
                    "type": "All",
                    "price": (min_price, max_price),
                    "sort_by": "Price (low→high)"
                }
                st.rerun()

            st.session_state.filters = {
                "city": selected_city,
                "type": selected_type,
                "price": selected_price,
                "sort_by": selected_sort,
            }

        properties = df.copy()
        # Apply search filter
        if search_term:
            properties = properties[properties["property_name"].str.contains(search_term, case=False, na=False)]
        
        # Apply other filters
        city_filter = st.session_state.filters["city"]
        type_filter = st.session_state.filters["type"]
        price_min, price_max = st.session_state.filters["price"]
        if city_filter != "All":
            properties = properties[properties["city"] == city_filter]
        if type_filter != "All":
            properties = properties[properties["property_type"] == type_filter]
        properties = properties[(properties["price"] >= price_min) & (properties["price"] <= price_max)]

        # Sorting
        sort_by = st.session_state.filters["sort_by"]
        if sort_by == "Price (low→high)":
            properties = properties.sort_values(by=["price", "property_name"], ascending=[True, True])
        elif sort_by == "Price (high→low)":
            properties = properties.sort_values(by=["price", "property_name"], ascending=[False, True])
        elif sort_by == "Area (high→low)":
            properties = properties.sort_values(by=["area_sqft", "property_name"], ascending=[False, True])
        elif sort_by == "Bedrooms (high→low)":
            properties = properties.sort_values(by=["bedrooms", "property_name"], ascending=[False, True])
        cards_per_row = 3
        rows = (len(properties) + cards_per_row - 1) // cards_per_row
        idx = 0
        for _ in range(rows):
            col_objs = st.columns(cards_per_row)
            for col in col_objs:
                if idx >= len(properties):
                    break
                row = properties.iloc[idx]
                with col.container(border=True):
                    # Image placeholder using seeded picsum for variety per listing
                    try:
                        seed = int(str(row['listing_id']).strip('P').lstrip('0') or 1)
                    except Exception:
                        seed = 1
                    st.image(f"https://picsum.photos/seed/{seed}/600/360", use_container_width=True)
                    st.markdown(f"**{row['property_name']}**")
                    st.caption(f"{row['property_type']} • {row['city']}")
                    specs = []
                    if int(row.get('bedrooms', 0)) > 0:
                        specs.append(f"{int(row['bedrooms'])} BR")
                    if int(row.get('bathrooms', 0)) > 0:
                        specs.append(f"{int(row['bathrooms'])} Bath")
                    if row.get('area_sqft'):
                        specs.append(f"{int(row['area_sqft'])} sqft")
                    if specs:
                        st.write(" • ".join(specs))
                    st.write(row["short_description"]) 
                    st.markdown(f"**Price:** {format_price(row['price'], row['price_currency'])}")
                    st.caption(f"Availability: {row['availability']}")
                    if st.button("Select for booking", key=f"select_{row['listing_id']}"):
                        st.session_state.selected_property_name = row['property_name']
                        st.toast(f"Selected {row['property_name']} for booking", icon="✅")
                idx += 1

    # ---------------- Booking Form ---------------- #
    st.markdown("---")
    st.subheader("📅 Book a Property Visit")

    with st.form("booking_form"):
        name = st.text_input("Your Name")
        property_options = df["property_name"].tolist()
        default_index = property_options.index(st.session_state.selected_property_name) if st.session_state.selected_property_name in property_options else 0
        property_name = st.selectbox("Select Property", property_options, index=default_index)
        date = st.date_input("Preferred Date")

        submitted = st.form_submit_button("✅ Book Now")

        if submitted:
            if name and property_name and date:
                save_booking(name, property_name, date)
                st.success(f"✅ Booking confirmed for **{name}** at **{property_name}** on **{date}**")
            else:
                st.error("⚠️ Please fill all fields.")

    # ---------------- View All Bookings ---------------- #
    st.markdown("---")
    st.subheader("📋 View All Bookings")

    bookings_df = load_bookings()
    if not bookings_df.empty:
        st.dataframe(bookings_df)
    else:
        st.write("No bookings yet.")

# Run app
if __name__ == "__main__":
    run_streamlit()
