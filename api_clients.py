import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from a .env file
load_dotenv()

# Load API key from environment variable
claude_api_key = os.getenv('CLAUDE_API_KEY')

def generate_response_claude(conversation_history, role, message, model_id, temperature, max_tokens):
    """
    Generate a response using Claude's Messages API.

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
    if not claude_api_key:
        raise ValueError("CLAUDE_API_KEY is not set in the environment variables.")

    client = Anthropic(api_key=claude_api_key)
    try:
        # Prepare the messages for Claude API
        messages = conversation_history + [{"role": role, "content": message}]

        response = client.messages.create(
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract the text content from the response
        if response.content and len(response.content) > 0:
            return response.content[0].text
        else:
            return ""
    except Exception as e:
        print(f"Error generating response from Claude: {str(e)}")
        return None

# You can add more API client functions here if needed