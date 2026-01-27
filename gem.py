import google.generativeai as genai
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('API_KEY'))

# System instrcuctions for the chatbot
system_instructions = """
You are a camera price‑tracking assistant.
Your job is to help users find prices for Canon, Sony, Nikon, and other cameras.
When the user asks for a camera price, call the get_camera_price() function
and return the result clearly and simply.
"""

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction=system_instructions
)

# -------------------------------
# eBay Buy API Price Lookup
# -------------------------------

def get_camera_price(camera_name):
    """
    Calls the eBay Buy Browse API to get the lowest price for a camera.
    """

    EBAY_TOKEN = os.getenv("EBAY_OAUTH_TOKEN")

    if not EBAY_TOKEN:
        return "Missing eBay OAuth token. Add it to your .env file."

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    params = {
        "q": camera_name,
        "limit": 3,
        "filter": "price:[100..5000]"  # avoid random junk listings
    }

    headers = {
        "Authorization": f"Bearer {EBAY_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        if "itemSummaries" not in data:
            return "No results found for that camera."

        item = data["itemSummaries"][0]

        title = item.get("title", "Unknown item")
        price = item.get("price", {}).get("value", "N/A")
        currency = item.get("price", {}).get("currency", "USD")
        link = item.get("itemWebUrl", "")

        return f"{title}\nPrice: {price} {currency}\nLink: {link}"

    except Exception as e:
        return f"Error fetching price: {e}"


# -------------------------------
# Chatbot Loop
# -------------------------------

def start_chat():
    chat_session = model.start_chat(history=[])

    print("📸 Camera Price Tracker Ready! (Type 'exit' to quit)")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Detect camera brand keywords
        brands = ["canon", "sony", "nikon", "fujifilm", "lumix", "panasonic"]

        if any(brand in user_input.lower() for brand in brands):
            price_info = get_camera_price(user_input)
            print(f"\n📷 Price Info:\n{price_info}\n")
            continue

        # Otherwise send to Gemini
        response = chat_session.send_message(user_input)
        print(f"\nAI: {response.text}\n")


if __name__ == "__main__":
    start_chat()
