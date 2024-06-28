# api_clients.py

import os
from dotenv import load_dotenv
import anthropic

# Load environment variables from a .env file
load_dotenv()

# Load API key from environment variable
claude_api_key = os.getenv('CLAUDE_API_KEY')

def generate_response_claude(conversation_history, role, message, model_id, temperature, max_tokens):
    """
    Generate a response using Claude's API.

    Args:
        conversation_history (list): History of the conversation.
        role (str): Role of the responder (e.g., user, assistant).
        message (str): The message to generate a response for.
        model_id (str): The model ID for Claude.
        temperature (float): Sampling temperature.
        max_tokens (int): Maximum number of tokens to generate.

    Returns:
        str: The generated response.
    """
    client = anthropic.Client(api_key=claude_api_key)
    try:
        # Prepare the messages for Claude API
        claude_messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
        claude_messages.append({"role": role, "content": message})

        response = client.messages.create(
            model=model_id,
            messages=claude_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error generating response from Claude: {str(e)}")
        return None