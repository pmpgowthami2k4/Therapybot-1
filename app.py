from flask import Flask, request, jsonify
import openai
from flask_cors import CORS
import random
from firebaseconfig import store_message  # ✅ Import function
from firebaseconfig import get_user_messages  # ✅ Import function

app = Flask(__name__)
CORS(app)  # Allow frontend to access backend

# ✅ OpenRouter API Key (Replace with your key)
api_key = "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"

# ✅ Set OpenRouter API Base URL
openai_client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# ✅ Function to Add Emojis to Responses
def add_emoji(response):
    emoji_map = {
        "sad": "😔",
        "happy": "😊",
        "anxious": "😟",
        "excited": "😃",
        "angry": "😠",
        "stress": "😩",
        "support": "🤗",
        "love": "❤️",
        "sorry": "☹️😟",
        "bullying": "😞",
        "understand": "🤍",
    }
    for word, emoji in emoji_map.items():
        if word in response.lower():
            return f"{response} {emoji}"
    return response

# ✅ API to Handle User Messages (No History Saved)
# @app.route("/chat", methods=["POST"])
# def chat():
#     user_input = request.json.get("message", "")
#     if not user_input:
#         return jsonify({"error": "Empty message"}), 400

#     try:
#         # ✅ Get Bot Response from OpenAI
#         response = openai_client.chat.completions.create(
#             model="openai/gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are Dr. Druggs, a compassionate therapy chatbot. Your purpose is to provide emotional support, coping strategies, mental health guidance, and healthcare guidance. You do not provide answers to general knowledge, science, politics, or any unrelated topics. If a user asks something off-topic, gently acknowledge their curiosity but redirect them by saying: 'That’s an interesting topic, but my focus is on emotional support. Let's talk about your feelings and well-being. How are you doing today?'"},
#                 {"role": "user", "content": user_input}
#             ]
#         )
#         bot_reply = response.choices[0].message.content
#         bot_reply_with_emoji = add_emoji(bot_reply)  # ✅ Add emoji

#         return jsonify({"reply": bot_reply_with_emoji})

#     except Exception as e:
#         print(f"❌ Error processing request: {e}")  # ✅ Debugging
#         return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    user_id = request.json.get("userId", "anonymous")  # Get user ID (default: anonymous)

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    try:
        # ✅ Get Bot Response from OpenAI
        response = openai_client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Dr. Druggs, a compassionate therapy chatbot."},
                {"role": "user", "content": user_input}
            ]
        )
        bot_reply = response.choices[0].message.content
        bot_reply_with_emoji = add_emoji(bot_reply)  # ✅ Add emoji

        # ✅ Store the chat in Firestore
        store_message(user_id, user_input, bot_reply_with_emoji)

        return jsonify({"reply": bot_reply_with_emoji})

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500
    
    @app.route("/chat-history", methods=["GET"])
    def chat_history():
        user_id = "test_user_123"  # ✅ Fixed ID for all messages
        messages = get_user_messages(user_id)
        return jsonify({"messages": messages})


# ✅ API to Handle Feel-Good Lists (Moved it ABOVE `app.run(debug=True)`)
@app.route("/feel-good-lists", methods=["GET"])
def feel_good_lists():
    feel_good_data = {
        "quote": random.choice([
            "You are capable of amazing things! 💪",
            "Happiness is not out there, it's in you! 😊",
            "You deserve love and kindness. ❤️",
            "You are special!!"
        ]),
        "song": random.choice([
            "🎶 'Here Comes the Sun' - The Beatles",
            "🎵 'Happy' - Pharrell Williams",
            "🎧 'Don't Stop Believin'' - Journey",
            "🎵 'Baby Shark dududdududu!!"
        ]),
        "activity": random.choice([
            "Take a deep breath and smile. 🌿",
            "Go for a 10-minute walk. 🚶‍♂️",
            "Take yourself on a beach date!!",
            "Write down three things you're grateful for. ✍️"
        ])
    }
    return jsonify(feel_good_data)

# ✅ Always keep this at the END of the file
if __name__ == "__main__":
    app.run(debug=True)
