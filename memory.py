import json
import os

CONVERSATION_FILE = "conversation.json"

def load_conversation():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_conversation(messages):
    with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def add_message(messages, role, content):
    messages.append({"role": role, "content": content})
    save_conversation(messages)
    return messages


# functionality test
# if __name__ == "__main__":
#     conv = load_conversation()
#     conv = add_message(conv, "user", "Salut!")
#     conv = add_message(conv, "assistant", "Bună ziua!")
#     print(conv)