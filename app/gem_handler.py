import google.generativeai as genai

MAX_RETRIES = 2

async def self_healing_stream_generator(model_name, gemini_params, api_key, safety_settings):
    """
    A generator that attempts to stream a response from the Gemini API, with self-healing capabilities.
    If the stream is interrupted, it retries the request with the conversation history.
    """
    chat_history = []
    retries = 0
    full_response_text = ""

    # Initial contents from the user
    initial_contents = gemini_params.get("contents", [])

    while retries <= MAX_RETRIES:
        try:
            # Configure the API key for each attempt
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name, safety_settings=safety_settings)

            # Combine history with the initial request for retries
            current_contents = initial_contents + chat_history
            
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
            chunk_count = 0
            async for chunk in response:
                yield chunk
                if chunk.text:
                    full_response_text += chunk.text
                chunk_count += 1
            
            # If we received chunks, the stream is considered successful for this attempt
            if chunk_count > 0:
                return

        except Exception as e:
            print(f"Stream interrupted on attempt {retries + 1}. Error: {e}. Retrying...")
            # Add the successfully received part of the response to history before retrying
            if full_response_text:
                chat_history.append({"role": "model", "parts": [full_response_text]})
                full_response_text = "" # Reset for the next retry

            # After the first attempt, subsequent retries should not include the initial user prompt again
            initial_contents = []

            retries += 1
            if retries > MAX_RETRIES:
                # After all retries, raise the last exception to be handled by the main endpoint
                raise e

        except Exception as e:
            print(f"Stream interrupted on attempt {retries + 1}. Error: {e}. Retrying...")
            retries += 1
            if retries > MAX_RETRIES:
                # After all retries, raise the last exception to be handled by the main endpoint
                raise e