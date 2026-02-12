import sys
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer

# -------------------------------
# Cyberpunk Theme Stylesheet
# -------------------------------
CYBERPUNK_STYLE = """
QWidget {
    background-color: #000000;
    color: #E0E0FF;
    font-family: 'Segoe UI';
}

/* Sidebar */
#sidebar {
    background-color: rgba(20, 0, 40, 0.35);
    border-right: 2px solid #7A00FF;
}

/* Sidebar Buttons */
QPushButton#sidebar_btn {
    background-color: rgba(40, 0, 80, 0.4);
    color: #D8B4FF;
    border: 1px solid #7A00FF;
    border-radius: 8px;
    padding: 10px;
}
QPushButton#sidebar_btn:hover {
    background-color: rgba(120, 0, 255, 0.5);
    border: 1px solid #C77DFF;
}

/* Chat Bubbles */
#bubble_text {
    background-color: rgba(60, 0, 120, 0.35);
    border: 1px solid #A64DFF;
    border-radius: 15px;
    padding: 10px;
    color: #E8D9FF;
    box-shadow: 0px 0px 12px #A64DFF;
    animation: pulse 2s infinite;
}

/* Reactive Pulse Animation */
@keyframes pulse {
    0% { box-shadow: 0 0 8px #A64DFF; }
    50% { box-shadow: 0 0 18px #C77DFF; }
    100% { box-shadow: 0 0 8px #A64DFF; }
}

/* AI Avatar */
#ai_avatar {
    border-radius: 10px;
    padding: 5px;
    background-color: rgba(80, 0, 160, 0.4);
    border: 1px solid #A64DFF;
    box-shadow: 0px 0px 10px #A64DFF;
}
"""

# -------------------------------
# Config / API Keys
# -------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
EBAY_TOKEN = os.getenv("EBAY_OAUTH_TOKEN")

genai.configure(api_key=API_KEY)

system_instructions = """
You are a friendly, knowledgeable camera assistant.
You help users with:
- Camera recommendations (beginner, intermediate, professional)
- Explaining differences between models
- Suggesting lenses and accessories
- Helping choose cameras for photography or video
- Answering general photography questions

You can:
- Recommend cameras for YouTube, travel, portraits, sports, vlogging, etc.
- Compare two cameras when the user types something like 'Canon R50 vs Sony A6400'
- Suggest lenses based on use case (portraits, low light, video, etc.)
- Explain specs like ISO, aperture, sensor size, frame rate, dynamic range.

You DO NOT call Python functions yourself. The app decides when to look up prices.
Speak naturally, conversationally, and clearly.
"""

model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction=system_instructions
)

chat_session = model.start_chat(history=[])

# -------------------------------
# Helpers: extract model
# -------------------------------
def extract_model(text: str) -> str:
    text = text.lower()

    remove_words = [
        "how much is the", "how much is a", "how much is",
        "how much does the", "how much does a", "how much does",
        "is how much", "what does it go for", "what does it sell for",
        "what is it worth", "what’s it worth", "price of", "cost of"
    ]
    for w in remove_words:
        text = text.replace(w, "")

    fillers = ["the", "a", "camera", "body", "kit", "cost", "price", "is"]
    for f in fillers:
        text = text.replace(f" {f} ", " ")

    return text.strip()

# -------------------------------
# eBay Price Lookup (Upgraded)
# -------------------------------
def get_camera_price(camera_name: str) -> str:
    if not EBAY_TOKEN:
        return "Your eBay OAuth token is missing or invalid."

    clean = extract_model(camera_name)

    search_terms = [
        clean,
        clean + " camera",
        clean + " body",
        clean + " kit",
        clean.upper(),
        clean.lower(),
        clean.replace("canon", "canon camera"),
        clean.replace("sony", "sony camera"),
        clean.replace("nikon", "nikon camera"),
    ]

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {EBAY_TOKEN}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }

    for term in search_terms:
        params = {
            "q": term,
            "limit": 10,
            "filter": "price:[50..5000]"
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            data = response.json()

            if "itemSummaries" in data and len(data["itemSummaries"]) > 0:
                item = data["itemSummaries"][0]
                title = item.get("title", "Unknown item")
                price = item.get("price", {}).get("value", "N/A")
                currency = item.get("price", {}).get("currency", "USD")
                link = item.get("itemWebUrl", "")

                return f"{title}\nPrice: {price} {currency}\nLink: {link}"

        except Exception as e:
            return f"Error contacting eBay: {e}"

    return f"No listings found for '{clean}'. Try being more specific."

# -------------------------------
# Chat Bubble Widget
# -------------------------------
class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, show_ai_avatar=False):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        if show_ai_avatar:
            avatar = QLabel("📷")
            avatar.setObjectName("ai_avatar")
            avatar.setAlignment(Qt.AlignmentFlag.AlignTop)
            avatar.setFixedSize(40, 40)
            font = QFont("Segoe UI", 18)
            avatar.setFont(font)
            layout.addWidget(avatar)

        bubble = QLabel(text)
        bubble.setObjectName("bubble_text")
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setMaximumWidth(350)
        bubble.setMinimumWidth(200)

        if is_user:
            bubble.setStyleSheet("""
                #bubble_text {
                    background-color: rgba(90, 0, 160, 0.7);
                    border: 1px solid #D48CFF;
                    border-radius: 15px;
                    padding: 10px;
                    color: #FFFFFF;
                    box-shadow: 0px 0px 12px #D48CFF;
                    animation: pulse 2s infinite;
                }
            """)
        layout.addWidget(bubble)
        layout.addStretch()

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(250)

# -------------------------------
# Main Chat Window
# -------------------------------
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📸 Cyberpunk AI Camera Assistant & Price Tracker")
        self.setFixedSize(700, 650)

        # XP / Level / Memory / Quiz state
        self.xp = 0
        self.level = 1
        self.memory = {
            "budget": None,
            "brand": None,
            "experience": None,
            "use_case": None,
            "size": None
        }
        self.quiz_active = False
        self.quiz_step = 0
        self.quiz_answers = {}

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(140)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        def make_btn(text):
            btn = QPushButton(text)
            btn.setObjectName("sidebar_btn")
            btn.setFixedHeight(40)
            return btn

        self.btn_home = make_btn("Home")
        self.btn_quiz = make_btn("Quiz")
        self.btn_price = make_btn("Prices")
        self.btn_compare = make_btn("Compare")
        self.btn_lens = make_btn("Lenses")
        self.btn_settings = make_btn("Settings")
        self.btn_xp = make_btn("XP: 0 | Lvl 1")

        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_quiz)
        sidebar_layout.addWidget(self.btn_price)
        sidebar_layout.addWidget(self.btn_compare)
        sidebar_layout.addWidget(self.btn_lens)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addWidget(self.btn_xp)
        sidebar_layout.addStretch()

        # Main layout with sidebar
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar)

        # Right side: chat + input
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.scroll)

        # Input row
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask about cameras, prices, or type 'quiz me'...")
        self.input_box.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_btn)
        right_layout.addLayout(input_layout)

        main_layout.addWidget(right_container)

        # Sidebar button actions
        self.btn_quiz.clicked.connect(lambda: self.start_quiz())
        self.btn_home.clicked.connect(lambda: self.finish_reply("Home: Ask me anything about cameras, prices, or lenses."))
        self.btn_price.clicked.connect(lambda: self.finish_reply("Price mode: ask 'how much is the Canon R8' or similar."))
        self.btn_compare.clicked.connect(lambda: self.finish_reply("Compare mode: type something like 'Canon R50 vs Sony A6400'."))
        self.btn_lens.clicked.connect(lambda: self.finish_reply("Lens guide: ask 'what lens for portraits' or 'best lens for low light'."))
        self.btn_settings.clicked.connect(lambda: self.finish_reply("Settings are minimal in this demo, but you can change how you ask questions."))

        self.setStyleSheet(CYBERPUNK_STYLE)

    # Memory helper
    def update_memory(self, key, value):
        self.memory[key] = value

    # XP system
    def add_xp(self, amount):
        self.xp += amount
        needed = self.level * 50
        if self.xp >= needed:
            self.level += 1
            self.finish_reply(f"🎉 You leveled up! You're now Level {self.level}!")
        self.btn_xp.setText(f"XP: {self.xp} | Lvl {self.level}")

    # Quiz system
    def start_quiz(self):
        if self.quiz_active:
            return
        self.quiz_active = True
        self.quiz_step = 1
        self.quiz_answers = {}
        self.finish_reply("🧪 Camera Finder Quiz started!\n\n1️⃣ What's your budget? (e.g. 800, 1200)")

    def handle_quiz(self, text):
        if self.quiz_step == 1:
            self.quiz_answers["budget"] = text
            self.update_memory("budget", text)
            self.quiz_step = 2
            return "2️⃣ Do you prefer photo, video, or both?"

        if self.quiz_step == 2:
            self.quiz_answers["use_case"] = text
            self.update_memory("use_case", text)
            self.quiz_step = 3
            return "3️⃣ Do you want a compact camera or a more professional body?"

        if self.quiz_step == 3:
            self.quiz_answers["size"] = text
            self.update_memory("size", text)
            self.quiz_step = 4
            return "4️⃣ What brand do you prefer? (Canon, Sony, Nikon, etc.)"

        if self.quiz_step == 4:
            self.quiz_answers["brand"] = text
            self.update_memory("brand", text)
            self.quiz_step = 5
            return "5️⃣ What's your experience level? (beginner / intermediate / pro)"

        if self.quiz_step == 5:
            self.quiz_answers["experience"] = text
            self.update_memory("experience", text)
            self.quiz_active = False
            self.add_xp(20)
            return self.ask_gemini(
                f"Based on these answers: {self.quiz_answers}, recommend the best camera and explain why in simple terms."
            )

        return "Quiz finished."

    # Add bubble
    def add_bubble(self, text, is_user=False):
        show_ai_avatar = not is_user
        bubble = ChatBubble(text, is_user=is_user, show_ai_avatar=show_ai_avatar)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        bubble.anim.setStartValue(QRect(-200, bubble.y(), bubble.width(), bubble.height()))
        bubble.anim.setEndValue(QRect(0, bubble.y(), bubble.width(), bubble.height()))
        bubble.anim.start()

        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

        return bubble

    # Typing animation
    def animate_typing(self, full_text, bubble):
        bubble_label = bubble.findChild(QLabel, "bubble_text")
        if bubble_label is None:
            return

        bubble_label.setText("")
        self.typing_index = 0

        def type_next():
            if self.typing_index <= len(full_text):
                bubble_label.setText(full_text[:self.typing_index])
                self.typing_index += 1
                self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                )
            else:
                self.typing_timer.stop()

        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(type_next)
        self.typing_timer.start(15)

    # Loading dots
    def show_loading(self):
        self.loading_bubble = self.add_bubble("AI is thinking", is_user=False)
        self.dot_count = 0

        def animate_dots():
            label = self.loading_bubble.findChild(QLabel, "bubble_text")
            if label:
                self.dot_count = (self.dot_count + 1) % 4
                label.setText("AI is thinking" + "." * self.dot_count)
                self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                )

        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(animate_dots)
        self.loading_timer.start(300)

    def hide_loading(self):
        if hasattr(self, "loading_timer"):
            self.loading_timer.stop()
        if hasattr(self, "loading_bubble"):
            self.loading_bubble.setParent(None)

    # Send message
    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        self.add_bubble(user_text, is_user=True)
        self.input_box.clear()

        self.show_loading()
        QTimer.singleShot(400, lambda: self.process_ai_reply(user_text))

    # Core AI logic
    def process_ai_reply(self, user_text):
        lower = user_text.lower()

        # Quiz flow
        if self.quiz_active:
            reply = self.handle_quiz(user_text)
            self.finish_reply(reply)
            return

        if "quiz" in lower or "quiz me" in lower:
            self.start_quiz()
            return

        # Memory capture
        if "my budget is" in lower:
            try:
                parts = lower.split("my budget is")[-1].strip()
                self.update_memory("budget", parts)
                self.finish_reply(f"Got it. I'll remember your budget is {parts}.")
                return
            except Exception:
                pass

        if "i prefer" in lower and "sony" in lower:
            self.update_memory("brand", "Sony")
            self.finish_reply("Nice, I'll prioritize Sony in my recommendations.")
            return

        if "i prefer" in lower and "canon" in lower:
            self.update_memory("brand", "Canon")
            self.finish_reply("Got it, I'll prioritize Canon in my recommendations.")
            return

        if "i am a beginner" in lower or "i'm a beginner" in lower:
            self.update_memory("experience", "beginner")
            self.finish_reply("Cool, I'll keep things beginner-friendly.")
            return

        # Help menu
        if lower in ["help", "commands", "menu"]:
            reply = (
                "Here’s what I can do:\n"
                "- Check camera prices\n"
                "- Recommend cameras\n"
                "- Compare cameras\n"
                "- Suggest lenses\n"
                "- Explain specs\n"
                "- Run a camera finder quiz (type 'quiz me')\n"
                "- Track XP and levels as you explore\n"
            )
            self.finish_reply(reply)
            return

        # Comparison
        if " vs " in lower:
            self.add_xp(15)
            reply = self.ask_gemini(f"Compare these two cameras: {user_text}")
            self.finish_reply(reply)
            return

        # Recommendations
        if "recommend" in lower or "best camera" in lower:
            context = {
                "memory": self.memory,
                "question": user_text
            }
            reply = self.ask_gemini(
                f"User context: {context}. Recommend a camera and explain why in simple terms."
            )
            self.finish_reply(reply)
            return

        # Lens suggestions
        if "lens" in lower:
            self.add_xp(5)
            reply = self.ask_gemini(f"Suggest lenses: {user_text}")
            self.finish_reply(reply)
            return

        # Limitations
        if lower == "limitations":
            reply = (
                "Limitations:\n"
                "- eBay prices may be inaccurate or outdated\n"
                "- AI may hallucinate specs\n"
                "- API tokens can expire\n"
                "- Requires internet\n"
            )
            self.finish_reply(reply)
            return

        # Test cases
        if lower == "test cases":
            reply = (
                "Test cases:\n"
                "1. How much is the Canon R50\n"
                "2. Best camera for YouTube under 1000\n"
                "3. Canon R50 vs Sony A6400\n"
                "4. What lens for portraits?\n"
                "5. quiz me\n"
            )
            self.finish_reply(reply)
            return

        # Summary
        if lower == "summary":
            reply = (
                "This project is a cyberpunk-themed AI camera assistant that combines "
                "Gemini reasoning with real-time eBay price data, memory of your preferences, "
                "a quiz mode, and an XP leveling system."
            )
            self.finish_reply(reply)
            return

        # Price detection
        price_phrases = [
            "how much", "price", "cost", "worth", "go for",
            "sell for", "buy", "deal", "value", "how expensive",
            "how much is a", "how much is the", "how much does",
            "is how much", "what does it go for", "what does it sell for",
            "what is it worth", "what’s it worth"
        ]

        brands = [
            "canon", "sony", "nikon", "fujifilm", "fuji",
            "lumix", "panasonic", "leica", "pentax", "sigma"
        ]

        camera_models = [
            "r8", "r6", "r5", "r10", "r50",
            "a7iii", "a7iv", "a6400", "a6600",
            "z30", "z50", "z5", "xs20"
        ]

        flat = lower.replace(" ", "")

        if (
            (any(b in lower for b in brands) or any(m in flat for m in camera_models))
            and any(p in lower for p in price_phrases)
        ):
            self.add_xp(10)
            reply = get_camera_price(user_text)
            self.finish_reply(reply)
            return

        # Default AI response
        reply = self.ask_gemini(user_text)
        self.finish_reply(reply)

    def ask_gemini(self, prompt):
        try:
            ai_response = chat_session.send_message(prompt)
            return ai_response.text if ai_response and ai_response.text else "I didn’t understand that."
        except Exception as e:
            return f"AI error: {e}"

    def finish_reply(self, reply):
        self.hide_loading()
        bubble = self.add_bubble("", is_user=False)
        self.animate_typing(reply, bubble)

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
