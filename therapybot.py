# 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
import openai

# Replace with your OpenRouter API Key
api_key = "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"

# Set OpenRouter API Base URL
openai_client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def chat_with_gpt(user_input):
    response = openai_client.chat.completions.create(
        model="openai/gpt-3.5-turbo",  # Change to another model if needed
        messages=[
            {"role": "system", "content": "You are a mental health chatbot providing emotional support."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

# Chat Loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    print("AI:", chat_with_gpt(user_input))
