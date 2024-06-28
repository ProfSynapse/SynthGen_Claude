import json
from api_clients import generate_response_claude

def analyze_conversation(conversation_history, config):
    """
    Analyze the completed conversation and generate labels with reasoning.

    Args:
        conversation_history (list): The complete conversation history.
        config (dict): Configuration settings.

    Returns:
        dict: A dictionary containing labels and their reasoning.
    """
    analysis_prompt = config['system_prompts']['conversation_analysis_prompt']
    
    full_prompt = f"{analysis_prompt}\n\nConversation History:\n{json.dumps(conversation_history, indent=2)}"

    analysis_response = generate_response_claude(
        [],  # Empty conversation history for the analysis
        "assistant",
        full_prompt,
        config['claude_details']['model_id'],
        config['generation_parameters']['temperature'],
        config['generation_parameters']['max_tokens']['analysis']
    )

    try:
        analysis_result = json.loads(analysis_response)
        return analysis_result
    except json.JSONDecodeError:
        print("Error: Unable to parse analysis response as JSON.")
        return None