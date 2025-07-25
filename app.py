# app.py - The Web Backend for Maitri
import os
import json
import requests
import subprocess
from datetime import datetime
import logging
from flask import Flask, render_template, request, jsonify

# --- Configuration ---
class Config:
    # --- NEW NAME: Changed from Jarvis to Maitri ---
    ASSISTANT_NAME = "Maitri"
    API_KEY = ("AIzaSyDDv_K0GmQeTUDIOhZ6ntJoYL_bcGeMiz8")
    MODEL = "gemini-1.5-flash-latest"
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    HEADERS = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}
    WEBSITES = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "wikipedia": "https://www.wikipedia.org"
    }

# --- Setup Logging and Flask App ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

if not Config.API_KEY:
    logging.critical("CRITICAL: GOOGLE_API_KEY environment variable not set.")

# --- Core AI and Command Logic ---
def call_llm(prompt):
    """Sends a prompt to the Google Gemini model and gets a response."""
    logging.info(f"Sending prompt to Gemini: '{prompt}'")
    # The new name is automatically used here
    system_prompt = f"You are {Config.ASSISTANT_NAME}, a helpful and friendly AI. Your name means 'friendliness'. Keep answers concise."
    full_prompt = f"{system_prompt}\n\nUser: {prompt}"
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    try:
        response = requests.post(Config.API_URL, headers=Config.HEADERS, data=json.dumps(payload), timeout=25)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logging.error(f"API request failed: {e}")
        return "I'm having trouble connecting to my brain right now."

def process_command(text):
    """
    Takes text input, processes it, and returns a JSON response.
    """
    command = text.lower()
    response_data = { "speak_text": "", "action_url": "" }

    if command.startswith("open"):
        target = command.replace("open", "").strip()
        if target in Config.WEBSITES:
            response_data["speak_text"] = f"Opening {target}."
            response_data["action_url"] = Config.WEBSITES[target]
            return jsonify(response_data)
        else:
            response_data["speak_text"] = f"Sorry, I can't open local applications like {target} from a web browser."
            return jsonify(response_data)

    if "what time is it" in command or "what's the time" in command:
        now = datetime.now().strftime("%I:%M %p")
        response_data["speak_text"] = f"The current time is {now}."
        return jsonify(response_data)
        
    response_data["speak_text"] = call_llm(command)
    return jsonify(response_data)

# --- Flask Web Routes ---
@app.route('/')
def index():
    """Renders the main web page."""
    return render_template('index.html', assistant_name=Config.ASSISTANT_NAME)

@app.route('/ask', methods=['POST'])
def ask():
    """Receives recognized speech and returns a JSON response."""
    data = request.get_json()
    user_text = data.get('text', '')
    logging.info(f"Received from web: '{user_text}'")

    if not user_text:
        return jsonify({"speak_text": "I didn't hear that. Please try again."})

    # Check for the new wake word "Maitri"
    if Config.ASSISTANT_NAME.lower() in user_text.lower():
        command = user_text.lower().replace(Config.ASSISTANT_NAME.lower(), "", 1).strip()
        if not command:
            return jsonify({"speak_text": "Yes? How can I help?"})
        return process_command(command)
    else:
        return jsonify({"speak_text": ""})

if __name__ == '__main__':
    app.run(debug=True, port=5000)