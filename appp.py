from flask import Flask, request, jsonify, render_template
import os
import json
import pyttsx3
from datetime import datetime
import subprocess
import platform

# Setup Groq API
import groq
groq.api_key = "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" 

app = Flask(__name__)

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

HISTORY_FILE = "chat_history.json"

def load_history():
    """Load chat history from file"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save chat history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def open_application(app_name):
    """Open applications on the system"""
    app_name = app_name.lower().strip()
    
    if platform.system() == "Windows":
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "vscode": "code.exe",
            "explorer": "explorer.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe"
        }
        
        if app_name in app_map:
            try:
                subprocess.Popen(app_map[app_name])
                return f"✓ Opened {app_name}"
            except Exception as e:
                return f"✗ Could not open {app_name}: {str(e)}"
    
    return f"Application '{app_name}' not found or not supported"

def speak(text):
    """Convert text to speech"""
    try:
        # Stop any ongoing speech first
        engine.stop()
        # Clear the speech queue
        engine.endLoop()
        # Say the new text
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

def stop_speech():
    """Stop any ongoing speech"""
    try:
        engine.stop()
        return True
    except Exception as e:
        print(f"Error stopping speech: {e}")
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    enable_voice = request.json.get("voice", False)
    
    # Load history
    history = load_history()
    
    # Check if user wants to open an app
    if user_message.lower().startswith("open "):
        app_to_open = user_message[5:]
        result = open_application(app_to_open)
        
        # Add to history
        history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": result,
            "type": "app"
        })
        save_history(history)
        
        if enable_voice:
            speak(result)
        
        return jsonify({"reply": result, "type": "app"})
    
    # Convert history to Groq format
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": 
                 item["user"] if i % 2 == 0 else item["assistant"]} 
                for i, item in enumerate(history) if "user" in item]
    messages.append({"role": "user", "content": user_message})
    
    try:
        client = groq.Groq(api_key=groq.api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast Groq model
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        
        # Save to history
        history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": reply,
            "type": "chat"
        })
        save_history(history)
        
        # Speak reply if voice enabled
        if enable_voice:
            speak(reply)
        
        return jsonify({"reply": reply, "type": "chat"})
    
    except Exception as e:
        # Demo mode fallback - intelligent responses without API
        user_lower = user_message.lower()
        
        # Generate contextual demo responses
        if any(word in user_lower for word in ["hello", "hi", "hey", "greet"]):
            demo_reply = "Hello! I'm Aarnav's AI Assistant. I'm currently in demo mode (API unavailable), but I can still help with chat history, voice control, and opening applications!"
        elif any(word in user_lower for word in ["name", "who are you"]):
            demo_reply = "I'm Aarnav's AI Assistant, a voice-enabled chatbot with app launching features!"
        elif any(word in user_lower for word in ["time", "date", "what time"]):
            demo_reply = f"The current time is: {datetime.now().strftime('%I:%M %p')}"
        elif any(word in user_lower for word in ["help", "what can you do"]):
            demo_reply = "I can: 💬 Chat with you, 🎤 Process voice input, 🚀 Open apps (say 'open notepad'), 📝 Save chat history!"
        else:
            demo_reply = f"Thanks for your message: '{user_message}'. I'm in demo mode but your message is saved! To use full AI features, please set up your OpenAI API key."
        
        # Save to history
        history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": demo_reply,
            "type": "chat"
        })
        save_history(history)
        
        if enable_voice:
            speak(demo_reply)
        
        return jsonify({"reply": demo_reply, "type": "chat"})

@app.route("/history", methods=["GET"])
def get_history():
    """Get all chat history"""
    history = load_history()
    return jsonify(history)

@app.route("/stop_speech", methods=["POST"])
def stop_speech_route():
    """Stop any ongoing speech"""
    success = stop_speech()
    return jsonify({"success": success})

@app.route("/speak", methods=["POST"])
def speak_text():
    """Speak a given text"""
    text = request.json.get("text", "")
    if text:
        try:
            speak(text)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "No text provided"})

@app.route("/new-topic", methods=["POST"])
def new_topic():
    """Start a new conversation topic by clearing history"""
    try:
        save_history([])  # Clear the conversation history
        return jsonify({"success": True, "message": "New conversation topic started"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/clear-history", methods=["POST"])
def clear_history():
    """Clear chat history"""
    save_history([])
    return jsonify({"message": "i am aarnav's AI assistant, and i have cleared all chat history! 🧹✨"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)