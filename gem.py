import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the API
genai.configure(api_key=os.getenv('API_KEY'))

# System message to define the persona
pirate_instructions = "You are a pirate chatbot. Respond only in pirate speak, using pirate slang and nautical terms. Do not reply in normal English."

# Initialize the model with system instructions
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    system_instruction=pirate_instructions
)

def start_chat():
    # Start a chat session to maintain context (optional but recommended)
    chat_session = model.start_chat(history=[])
    
    print("Ahoy! The salty dog is ready to chat. (Type 'exit' to abandon ship)")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Fair winds and following seas, matey!")
            break
        
        try:
            # Send message to the model
            response = chat_session.send_message(user_input)
            print(f"\nPirate: {response.text}\n")
        except Exception as e:
            print(f"Blimey! An error occurred: {e}")

if __name__ == "__main__":
    start_chat()
