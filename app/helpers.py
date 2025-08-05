from typing import List, Dict
import random
import string

# Gemini 1.0 安全设置
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]

# Gemini 2.0 安全设置
SAFETY_SETTINGS_G2 = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]

def get_safety_settings(model_name: str) -> List[Dict[str, str]]:
    if model_name.startswith('gemini-2'):
        return SAFETY_SETTINGS_G2
    return SAFETY_SETTINGS

def openai_to_gemini_params(openai_request: dict) -> dict:
    """Converts OpenAI-compatible request parameters to Gemini format."""
    gemini_params = {}
    
    generation_config = {
        "temperature": openai_request.get("temperature"),
        "top_p": openai_request.get("top_p"),
    }

    if "max_tokens" in openai_request and openai_request["max_tokens"] is not None:
        generation_config["max_output_tokens"] = openai_request["max_tokens"]

    gemini_params["generation_config"] = {k: v for k, v in generation_config.items() if v is not None}

    messages = openai_request.get("messages", [])
    system_instruction = None
    gemini_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
            break

    last_user_message_index = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "user":
            last_user_message_index = i
            break

    for i, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if i == last_user_message_index:
                random_prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                content = f"{random_prefix}\n{content}"
            gemini_messages.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            gemini_messages.append({"role": "model", "parts": [{"text": content}]})

    gemini_params["system_instruction"] = system_instruction
    gemini_params["contents"] = gemini_messages
    
    return gemini_params