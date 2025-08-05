import google.generativeai as genai

MAX_RETRIES = 2

import logging

logger = logging.getLogger("app")

async def self_healing_stream_generator(model_name, gemini_params, api_key):
    """
    A generator that attempts to stream a response from the Gemini API, with self-healing capabilities.
    If the stream is interrupted, it retries the request with the conversation history.
    """
    chat_history = []
    retries = 0
    full_response_text = ""

    # Initial contents from the user
    initial_contents = gemini_params.get("contents", [])

    logger.info(f"Initiating self-healing stream for model: {model_name}")
    while retries <= MAX_RETRIES:
        try:
            # Configure the API key for each attempt
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)

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
                # Ensure the chunk has content before trying to access .text
                if chunk.parts:
                    full_response_text += chunk.text
                chunk_count += 1
            
            # If we received chunks, the stream is considered successful for this attempt
            if chunk_count > 0 and (not response.prompt_feedback or response.prompt_feedback.block_reason != 'SAFETY'):
                logger.info("Stream completed successfully.")
                return

        except Exception as e:
            logger.warning(f"Stream interrupted on attempt {retries + 1}. Error: {e}. Retrying...")
            # Add the successfully received part of the response to history before retrying
            if full_response_text:
                chat_history.append({"role": "model", "parts": [full_response_text]})
                # Add a user message to guide the model to continue
                chat_history.append({"role": "user", "parts": ["Please continue generating the response from where you left off."]})
                full_response_text = "" # Reset for the next retry

            retries += 1
            if retries > MAX_RETRIES:
                logger.error("All retries failed.")
                # After all retries, raise the last exception to be handled by the main endpoint
                raise e

        except Exception as e:
            print(f"Stream interrupted on attempt {retries + 1}. Error: {e}. Retrying...")
            retries += 1
            if retries > MAX_RETRIES:
                # After all retries, raise the last exception to be handled by the main endpoint
                raise e