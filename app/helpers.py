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

    # Add a random prefix to the last user message to prevent cache hits
    if messages and messages[-1]["role"] == "user":
        last_content = messages[-1].get("content", "")
        if isinstance(last_content, str):
            random_prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            messages[-1]["content"] = f"{random_prefix}\n{last_content}"

    system_instruction = None
    gemini_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
            break

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        # Skip system messages as they are handled separately
        if role == "system":
            continue
        
        # Gemini API expects 'model' for assistant role
        gemini_role = "model" if role == "assistant" else role
        
        # Per Gemini API documentation, parts should be a list of dicts with a 'text' key
        if isinstance(content, str):
            gemini_messages.append({"role": gemini_role, "parts": [{"text": content}]})
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append({"text": item["text"]})
            gemini_messages.append({"role": gemini_role, "parts": parts})

    gemini_params["system_instruction"] = system_instruction
    gemini_params["contents"] = gemini_messages
    
    return gemini_params