import os
import json
import random
import uuid
from api_clients import generate_response_claude
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Load API key from environment variable
claude_api_key = os.getenv('CLAUDE_API_KEY')

def generate_response(role, message, response_type=None, model_conversation_history=None, config=None):
    """
    Generate a response using Claude.

    Args:
        role (str): The role of the responder (e.g., user, assistant).
        message (str): The message to generate a response for.
        response_type (str, optional): The type of response to generate.
        model_conversation_history (list, optional): The history of the conversation for the model.
        config (dict, optional): Configuration settings.

    Returns:
        str: The generated response.
    """
    if not isinstance(config['generation_parameters']['max_tokens'], dict):
        raise ValueError("config['generation_parameters']['max_tokens'] should be a dictionary")

    max_tokens = config['generation_parameters']['max_tokens'].get(response_type or role, config['generation_parameters']['max_tokens']['default'])

    try:
        return generate_response_claude(
            model_conversation_history or [],
            role,
            message,
            config['claude_details']['model_id'],
            config['generation_parameters']['temperature'],
            max_tokens
        )
    except Exception as e:
        print(f"Error generating response from Claude: {str(e)}")
        return None

def append_conversation_to_json(conversation, output_file, conversation_id):
    """
    Append a conversation entry to a JSON file.

    Args:
        conversation (dict): The conversation entry to append.
        output_file (str): Path to the output JSON file.
        conversation_id (str): The ID of the conversation.
    """
    conversations = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                conversations = json.load(f)
            except json.JSONDecodeError:
                conversations = []

    conversations.append(conversation)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, indent=4)

def generate_and_append_response(role, prompt, model_conversation_history, user_conversation_history, output_file, conversation_id, turn, response_type, config):
    """
    Generate a response and append it to the conversation history.

    Args:
        role (str): The role of the responder (e.g., user, assistant).
        prompt (str): The prompt for generating the response.
        model_conversation_history (list): The history of the conversation for the model.
        user_conversation_history (list): The history of the user's conversation.
        output_file (str): The output file path.
        conversation_id (str): The conversation ID.
        turn (int): The turn number in the conversation.
        response_type (str): The type of response to generate.
        config (dict): Configuration settings.

    Returns:
        tuple: The generated response and the new last_role.
    """
    print(f"Conversation ID: {conversation_id}, Turn: {turn}, Role: {role}")
    print(random.choice(config['synapse_thoughts']))

    # Get character names from config
    cor_name = config['character_names']['cor']
    assistant_name = config['character_names']['assistant']
    user_name = config['character_names']['user']

    # Determine the name based on the role and response_type
    if role == "user":
        name = user_name
    elif response_type == "cor":
        name = cor_name
    elif response_type == "professor_synapse":
        name = assistant_name
    else:
        name = "System"

    # Get the last role from the conversation history
    last_role = model_conversation_history[-1]['role'] if model_conversation_history else "system"

    # Ensure alternating roles for Claude API
    if role == last_role:
        # If the roles would be the same, insert a user message
        interim_prompt = f"Based on the last response, what would be a good follow-up question or comment?"
        interim_response = generate_response("user", interim_prompt, model_conversation_history=model_conversation_history, config=config)
        model_conversation_history.append({"role": "user", "content": interim_response})
        user_conversation_history.append({"role": "user", "content": interim_response, "name": "System"})
        append_conversation_to_json({"role": "user", "name": "System", "content": interim_response, "conversation_id": conversation_id, "turn": turn, "token_count": len(interim_response)}, output_file, conversation_id)
        last_role = "user"

    response = generate_response(role, prompt, response_type, model_conversation_history, config)
    if response is None:
        print(f"Failed to generate {role} response.")
        return None, last_role

    if name == assistant_name:
        response = f"{config['character_names']['assistant_prefix']}: {response}"

    model_conversation_history.append({"role": role, "content": response})
    
    if role == "user" or name == assistant_name:
        user_conversation_history.append({"role": role, "content": response, "name": name})
    
    append_conversation_to_json({"role": role, "name": name, "content": response, "conversation_id": conversation_id, "turn": turn, "token_count": len(response)}, output_file, conversation_id)
    
    return response, role

def generate_conversation(file_content, output_file, config):
    """
    Generate a synthetic conversation based on a file's content.

    Args:
        file_content (dict): File content to base the conversation on.
        output_file (str): Path to the output file for saving the conversation.
        config (dict): Configuration settings.

    Returns:
        list: The generated conversation history.
    """
    model_conversation_history = []
    user_conversation_history = []
    conversation_id = str(uuid.uuid4())
    last_role = "system"  # Initialize with system to ensure the first message is from the user

    user_name = config['character_names']['user']
    assistant_name = config['character_names']['assistant']

    # Initial user problem generation with file content access
    print(f"Generating user problem for file: {file_content['filename']}")
    user_problem, last_role = generate_and_append_response(
        "user",
        f"{config['system_prompts']['user_system_prompt']}\n\nFile Content:\n{file_content['content']}\n\n**You are now {user_name}!**, and are about to begin your conversation with {assistant_name}. Come up with the problem you face based on the provided text, and respond in the first person as {user_name}:**",
        model_conversation_history,
        user_conversation_history,
        output_file,
        conversation_id,
        0,
        response_type="user",
        config=config
    )
    
    if user_problem is None or not user_problem.strip():
        print("Failed to generate user problem or user problem is empty.")
        return None

    num_turns = random.randint(6, 10)  # Randomly choose the number of turns between 6 and 10

    for turn in range(1, num_turns + 1):
        print(f"Generating CoR response for turn {turn}")
        cor_prompt = f"{config['system_prompts']['cor_system_prompt']}\n\nConversation History:\n{json.dumps(model_conversation_history)}\n\nFilled-in CoR:"
        cor_response, last_role = generate_and_append_response(
            "assistant",
            cor_prompt,
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn,
            response_type="reasoning",
            config=config
        )
        if cor_response is None or not cor_response.strip():
            return model_conversation_history

        print(f"Generating {assistant_name} response for turn {turn}")
        synapse_prompt = f"{config['system_prompts']['synapse_system_prompt']}\n\nConversation History:\n{json.dumps(model_conversation_history)}\n\n{config['character_names']['assistant_prefix']}:"
        synapse_response, last_role = generate_and_append_response(
            "assistant",
            synapse_prompt,
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn,
            response_type="assistant",
            config=config
        )
        if synapse_response is None or not synapse_response.strip():
            return model_conversation_history

        # User follow-up prompt without file content access but using the system prompt and previous user conversation history
        user_followup_prompt = f"{config['system_prompts']['user_system_prompt']}\n\nConversation History:\n{json.dumps(user_conversation_history)}\n\nBased on {assistant_name}'s previous response, ask a specific NEW question that builds upon the information provided and helps deepen your understanding of the topic. Respond in first person as {user_name}:"
        user_followup_response, last_role = generate_and_append_response(
            "user",
            user_followup_prompt,
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn,
            response_type="user",
            config=config
        )
        if user_followup_response is None or not user_followup_response.strip():
            return model_conversation_history

    return model_conversation_history

def format_output(conversation):
    """
    Format the output of the conversation.

    Args:
        conversation (list): The conversation history.

    Returns:
        list: The formatted conversation history.
    """
    return conversation