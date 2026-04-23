from dotenv import load_dotenv
from google import genai
from memory import load_conversation, add_message
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def chat(user_input):
    # Încarcă istoricul din fișier
    messages = load_conversation()
    
    # Adaugă mesajul nou al utilizatorului
    messages = add_message(messages, "user", user_input)
    
    # Construiește textul complet al conversației
    conversation_text = ""
    for message in messages:
        role = message["role"]
        content = message["content"]
        conversation_text += f"{role}: {content}\n"
    
    # Trimite tot istoricul la AI
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=conversation_text,
    )
    
    ai_response = response.text
    
    # Salvează răspunsul AI în memorie
    add_message(messages, "assistant", ai_response)
    
    return ai_response


# Test
# if __name__ == "__main__":
#     print(chat("Salut! Mă cheamă Lorena."))
#     print(chat("Cum mă cheamă?"))