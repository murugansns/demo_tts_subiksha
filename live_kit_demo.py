from flask import Flask, request, jsonify
import threading
import requests
import livekit

import time

LIVEKIT_URL = "wss://demo-tymfvw1x.livekit.cloud"
LIVEKIT_API_KEY = "APIzunoPLtAuHfG"
LIVEKIT_API_SECRET = "TgGM3e0ru5zJjZpswxilB7TG3WG1ec9bWepNJDjLBFfC"

app = Flask(__name__)


# Flask API to validate and trim audio
@app.route('/validate_audio', methods=['POST'])
def validate_audio():
    data = request.json
    length = data.get("length", 0)

    if length > 60:
        return jsonify({"processed_audio": "Trimmed audio segment due to exceeding length"}), 200

    return jsonify({"processed_audio": "Original audio"}), 200


# Function to estimate audio length based on text
def estimate_audio_length(text):
    words_per_second = 2  # Adjust based on TTS speech rate
    estimated_length = len(text.split()) / words_per_second
    return estimated_length


# Callback function before text to speech processing
def before_tts_cb(session, text):
    estimated_length = estimate_audio_length(text)

    # Send the estimated length to the backend for validation
    backend_url = "http://localhost:8585/validate_audio"
    response = requests.post(backend_url, json={"length": estimated_length})

    if response.status_code == 200:
        return response.json().get("processed_audio", text)

    return text  # Fallback if backend fails


# Function to start Flask in a separate thread
def run_flask():
    app.run(port=8585)


if __name__ == "__main__":
    # Start Flask server in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Wait for Flask to start
    time.sleep(2)

    # Initialize LiveKit Voice Pipeline Agent
    agent = livekit.VoicePipelineAgent(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    agent.before_tts_callback = before_tts_cb
    print("LiveKit Voice Pipeline Agent Running...\n")

    # CLI for User Input
    while True:
        user_input = input("Enter text for TTS (type 'exit' to quit): ")

        if user_input.lower() == "exit":
            print("Exiting...")
            break

        session = None  # Assuming a session can be created or retrieved
        processed_text = before_tts_cb(session, user_input)

        print(f"Processed Text: {processed_text}")

    agent.stop()  # Stop the LiveKit agent before exiting
