from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from flask_cors import CORS
import json
import logging
import re
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)  # Fixed _name_ → __name__
CORS(app)

# Load API key securely from environment variables
API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyAE4UdXbKigWNn0fJzi2CFthVeObdH3glQ")  # Replace or set as env var

class RoadsideAssistanceBot:
    def __init__(self, api_key):  # Fixed _init_ → __init__
        self.api_key = api_key
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logging.info("Model configured successfully.")
        except Exception as e:
            logging.error(f"Error configuring model: {str(e)}")

        # Context for chatbot responses
        self.base_context = """
        You are an AI-based roadside assistance chatbot.
        Your role:
        1. Diagnose vehicle issues and suggest solutions.
        2. Provide structured responses with:
           - Problem description
           - Severity (High, Medium, Low)
           - Steps to fix the issue
           - Warnings & safety measures
           - Additional notes
        3. Assist with:
           - Battery issues, Tire punctures, Engine problems
           - Brake failures, Overheating, Fuel problems
           - Electrical malfunctions, Warning lights
           - Fluid leaks, Emergency towing
        4. Keep responses concise, clear, and practical.
        """

    def clean_response(self, text):
        """Cleans and formats chatbot responses."""
        text = re.sub(r'\*+', '', text)  # Remove markdown formatting
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'`+', '', text)

        sections = ['Problem', 'Severity', 'Steps to resolve', 'Warning/Precaution', 'Additional Notes']
        for section in sections:
            text = re.sub(f"{section}:", f"\n\n{section}:\n", text)  # Add spacing for readability

        return text.strip()

    def generate_response(self, user_input):
        """Generates chatbot response based on user input."""
        try:
            full_prompt = f"""
            {self.base_context}
            User Query: {user_input}
            Provide a structured response with relevant details.
            """
            logging.debug(f"Prompt: {full_prompt[:100]}...")  # Log first 100 chars
            response = self.model.generate_content(full_prompt)
            response_text = response.text if response else "Error: No response generated."

            cleaned_response = self.clean_response(response_text)
            self.save_conversation(user_input, cleaned_response)

            return cleaned_response
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return "Sorry, I encountered an error processing your request."

    def save_conversation(self, user_input, bot_response):
        """Saves conversation history to a JSON file."""
        try:
            conversations = []
            if os.path.exists("conversations.json"):
                with open("conversations.json", "r") as f:
                    conversations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            conversations = []

        conversations.append({"user_input": user_input, "bot_response": bot_response})

        try:
            with open("conversations.json", "w") as f:
                json.dump(conversations, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving conversation: {str(e)}")

# Initialize chatbot
bot = RoadsideAssistanceBot(api_key=API_KEY)

@app.route('/')
def home():
    return """
    <h1>Welcome to Roadside Assistance Chatbot</h1>
    <p>Use POST /chat endpoint to interact with the bot.</p>
    """

@app.route('/test')
def test():
    return jsonify({"status": "success", "message": "API is working correctly"})

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Handles chatbot interactions."""
    if request.method == 'GET':
        return render_template('chat.html')  # Ensure 'templates/chat.html' exists
    elif request.method == 'POST':
        try:
            data = request.get_json()
            user_input = data.get("message", "").strip()

            if not user_input:
                return jsonify({"error": "No message provided"}), 400

            response = bot.generate_response(user_input)
            return jsonify({"response": response})
        except Exception as e:
            logging.error(f"Error in /chat endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/chat-interface')
def chat_interface():
    return render_template('chat.html')

if __name__ == "__main__":  # Fixed _name_ → __name__, _main_ → __main__
    print("Starting Roadside Assistance Chatbot API...")
    app.run(debug=True, host='0.0.0.0', port=8000)
