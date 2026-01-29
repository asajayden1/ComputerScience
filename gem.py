import sys
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

# -------------------------------
# Load API Keys
# -------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

system_instructions = """
You are a camera price‑tracking assistant.
Your job is to help users find prices for Canon, Sony, Nikon, and other cameras.
"""

model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction=system_instructions
)

chat_session = model.start_chat(history=[])

# -------------------------------
# eBay Price Lookup
# -------------------------------
def get_camera_price(camera_name):
    EBAY_TOKEN = os.getenv("EBAY_OAUTH_TOKEN")
    if not EBAY_TOKEN:
        return "Missing eBay OAuth token."

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {"q": camera_name, "limit": 3}
    headers = {
        "Authorization": f"Bearer {EBAY_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }

    try:
        data = requests.get(url, params=params, headers=headers).json()
        if "itemSummaries" not in data:
            return "No results found."

        item = data["itemSummaries"][0]
        title = item.get("title", "Unknown item")
        price = item.get("price", {}).get("value", "N/A")
        currency = item.get("price", {}).get("currency", "USD")
        link = item.get("itemWebUrl", "")

        return f"{title}\nPrice: {price} {currency}\nLink: {link}"

    except Exception as e:
        return f"Error: {e}"

# -------------------------------
# Rounded Chat Bubble Widget
# -------------------------------
class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, icon_path=None):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)

        if icon_path:
            icon = QLabel()
            pix = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon.setPixmap(pix)
            layout.addWidget(icon)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))

        if is_user:
            bubble.setStyleSheet("""
                background-color: #4A90E2;
                color: white;
                padding: 10px;
                border-radius: 15px;
            """)
        else:
            bubble.setStyleSheet("""
                background-color: #EAEAEA;
                color: black;
                padding: 10px;
                border-radius: 15px;
            """)

        layout.addWidget(bubble)
        layout.addStretch()

# -------------------------------
# Main Chat Window
# -------------------------------
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📸 Camera Price Tracker")
        self.setGeometry(200, 200, 500, 650)

        main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll)

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask about a camera...")
        self.input_box.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_btn)
        main_layout.addLayout(input_layout)

    def add_bubble(self, text, is_user=False):
        icon = "user_icon.png" if is_user else "ai_icon.png"
        bubble = ChatBubble(text, is_user=is_user, icon_path=icon)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        self.add_bubble(user_text, is_user=True)
        self.input_box.clear()

        brands = ["canon", "sony", "nikon", "fujifilm", "lumix", "panasonic"]
        if any(b in user_text.lower() for b in brands):
            reply = get_camera_price(user_text)
        else:
            reply = chat_session.send_message(user_text).text

        self.add_bubble(reply, is_user=False)

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
