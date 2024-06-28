import os
import json
import random
import uuid
from api_clients import generate_response_claude
from conversation_analysis import analyze_conversation
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
    print(f"Conversation ID: {conversation_id}, Turn: {turn}, Role: {role}, Response Type: {response_type}")
    
    cor_name = config['character_names']['cor']
    assistant_name = config['character_names']['assistant']
    user_name = config['character_names']['user']
    assistant_prefix = config['character_names']['assistant_prefix']

    # Determine the name based on the role and response_type
    if response_type == "user_cor" or response_type == "reasoning":
        name = cor_name
        api_role = "user" if response_type == "user_cor" else "assistant"
    elif response_type == "assistant":
        name = assistant_name
        api_role = "assistant"
    else:
        name = user_name
        api_role = "user"

    response = generate_response(api_role, prompt, response_type, model_conversation_history, config)
    if response is None:
        print(f"Failed to generate {role} response.")
        return None, api_role

    if name == assistant_name:
        response = f"{assistant_prefix}: {response}"

    model_conversation_history.append({"role": api_role, "content": response})
    
    user_conversation_history.append({"role": api_role, "content": response, "name": name})
    
    append_conversation_to_json({"role": api_role, "name": name, "content": response, "conversation_id": conversation_id, "turn": turn, "token_count": len(response)}, output_file, conversation_id)
    
    return response, api_role

def generate_conversation(file_content, output_file, config):
    model_conversation_history = []
    user_conversation_history = []
    conversation_id = str(uuid.uuid4())

    cor_name = config['character_names']['cor']
    assistant_name = config['character_names']['assistant']
    user_name = config['character_names']['user']
    assistant_prefix = config['character_names']['assistant_prefix']

    # 1. User problem generation
    print("1. Generating initial user problem")
    problem_generation_prompt = config['system_prompts']['user_problem_generation_prompt']
    initial_problem, _ = generate_and_append_response(
        "user",
        f"{problem_generation_prompt}\n\nFile Content:\n{file_content['content']}",
        model_conversation_history,
        user_conversation_history,
        output_file,
        conversation_id,
        0,
        response_type="problem_generation",
        config=config
    )
    
    if initial_problem is None or not initial_problem.strip():
        print("Failed to generate initial problem.")
        return None

    # 2. User response in character to the initial problem
    print("2. Generating User response to initial problem")
    user_prompt = config['system_prompts']['user_system_prompt']
    user_response, _ = generate_and_append_response(
        "user",
        f"{user_prompt}\n\nProblem: {initial_problem}\n\nRespond as {user_name} to this problem:",
        model_conversation_history,
        user_conversation_history,
        output_file,
        conversation_id,
        1,
        response_type="user",
        config=config
    )
    
    if user_response is None or not user_response.strip():
        print("Failed to generate user response.")
        return model_conversation_history

    num_turns = random.randint(3, 5)  # Randomly choose the number of turns
    print(f"Generating conversation with {num_turns} turns")

    for turn in range(num_turns):
        # 3. CoR response
        print(f"Turn {turn + 1}, Step 3: Generating {cor_name} Response")
        cor_prompt = config['system_prompts']['cor_system_prompt']
        cor_response, _ = generate_and_append_response(
            "assistant",
            f"{cor_prompt}\n\nConversation History:\n{json.dumps(model_conversation_history)}\n\nFile Content:\n{file_content['content']}\n\nGenerated Chain of Reasoning response:",
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn * 4 + 2,
            response_type="reasoning",
            config=config
        )
        if cor_response is None or not cor_response.strip():
            print(f"Failed to generate {cor_name} response at turn {turn + 1}.")
            return model_conversation_history

        # 4. Professor Synapse response
        print(f"Turn {turn + 1}, Step 4: Generating {assistant_name} Response")
        synapse_prompt = config['system_prompts']['synapse_system_prompt']
        synapse_response, _ = generate_and_append_response(
            "assistant",
            f"{synapse_prompt}\n\nConversation History:\n{json.dumps(model_conversation_history)}\n\n{assistant_prefix}:",
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn * 4 + 3,
            response_type="assistant",
            config=config
        )
        if synapse_response is None or not synapse_response.strip():
            print(f"Failed to generate {assistant_name} response at turn {turn + 1}.")
            return model_conversation_history

        # 5. User problem follow-up
        print(f"Turn {turn + 1}, Step 5: Generating user problem follow-up")
        followup_prompt = config['system_prompts']['user_problem_follow_up']
        followup_problem, _ = generate_and_append_response(
            "user",
            f"{followup_prompt}\n\nConversation History:\n{json.dumps(user_conversation_history)}\n\nGenerated follow-up problem or question:",
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn * 4 + 4,
            response_type="problem_generation",
            config=config
        )
        if followup_problem is None or not followup_problem.strip():
            print(f"Failed to generate follow-up problem at turn {turn + 1}.")
            return model_conversation_history

        # 6. User follow-up response
        print(f"Turn {turn + 1}, Step 6: Generating {user_name} follow-up response")
        user_followup_prompt = config['system_prompts']['user_system_prompt']
        user_followup_response, _ = generate_and_append_response(
            "user",
            f"{user_followup_prompt}Conversation History:\n{json.dumps(user_conversation_history)}\n\nProblem: {followup_problem}\n\nRespond as {user_name} putting this follow-up problem in your own words:",
            model_conversation_history,
            user_conversation_history,
            output_file,
            conversation_id,
            turn * 4 + 5,
            response_type="user",
            config=config
        )
        if user_followup_response is None or not user_followup_response.strip():
            print(f"Failed to generate {user_name} follow-up response at turn {turn + 1}.")
            return model_conversation_history

    print("Completed all turns")
    
    # Analyze the conversation
    analysis_result = analyze_conversation(model_conversation_history, config)
    
    if analysis_result:
        # Append the analysis result to the conversation history
        model_conversation_history.append({
            "role": "system",
            "content": "Conversation Analysis",
            "analysis": analysis_result
        })
        
        # Append the analysis to the output file
        append_conversation_to_json({
            "role": "system",
            "name": "Conversation Analysis",
            "content": json.dumps(analysis_result, indent=2),
            "conversation_id": conversation_id,
            "turn": len(model_conversation_history),
            "token_count": len(json.dumps(analysis_result))
        }, output_file, conversation_id)
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