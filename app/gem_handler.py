import google.generativeai as genai

MAX_RETRIES = 2

async def self_healing_stream_generator(model_name, gemini_params, api_key):
    """
    A generator that attempts to stream a response from the Gemini API, with self-healing capabilities.
    If the stream is interrupted, it retries the request with the conversation history.
    """
    chat_history = []
    retries = 0

    # Initial contents from the user
    initial_contents = gemini_params.get("contents", [])

    while retries <= MAX_RETRIES:
        try:
            # Configure the API key for each attempt
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)

            # Combine history with the initial request for retries
            current_contents = chat_history + initial_contents
            
            # Create a new set of params for the attempt
            attempt_params = gemini_params.copy()
            attempt_params["contents"] = current_contents

            # Generate content and stream the response
            response = await model.generate_content_async(
                attempt_params["contents"],
                generation_config=attempt_params.get("generation_config"),
                stream=True
            )

            # Stream and collect history
            async for chunk in response:
                yield chunk
                if chunk.parts:
                    # This logic assumes the 'content' structure is suitable for history.
                    # It might need adjustment based on the actual API response structure.
                    chat_history.append({"role": "model", "parts": [part.to_dict() for part in chunk.parts]})

            # If the stream completes without error, break the loop
            return

        except Exception as e:
            print(f"Stream interrupted on attempt {retries + 1}. Error: {e}. Retrying...")
            retries += 1
            if retries > MAX_RETRIES:
                # After all retries, raise the last exception to be handled by the main endpoint
                raise e