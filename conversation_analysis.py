import json
import traceback
from api_clients import generate_response_claude

def analyze_conversation(output_file, config):
    try:
        # Read the existing conversation from the JSON file
        with open(output_file, 'r') as f:
            conversation = json.load(f)
        print(f"Successfully loaded conversation from {output_file}")

        # Extract the conversation history
        conversation_history = json.dumps(conversation, indent=2)
        print(f"Conversation history extracted, length: {len(conversation_history)}")

        # Prepare the prompts
        system_prompt = config['system_prompts']['conversation_analysis_prompt']
        user_prompt = f"Analyze the following conversation:\n\n{conversation_history}"
        
        print("System prompt:", system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt)
        print("User prompt length:", len(user_prompt))

        # Generate the analysis
        analysis_response = generate_response_claude(
            [{"role": "user", "content": user_prompt}],  # Start with a user message
            "assistant",  # Request response as assistant
            "",  # Empty message as we've included the prompt in conversation_history
            config['claude_details']['model_id'],
            config['generation_parameters']['temperature'],
            config['generation_parameters']['max_tokens']['analysis'],
            system_prompt  # Pass system prompt separately
        )
        
        print("Raw analysis response:")
        print(analysis_response)
        print("Analysis response received, length:", len(analysis_response) if analysis_response else "No response")

        if analysis_response is None:
            raise ValueError("No response received from Claude API")

        # Try to parse the response as JSON, if it fails, use the raw response
        try:
            analysis_result = json.loads(analysis_response)
            print("Analysis response successfully parsed as JSON")
        except json.JSONDecodeError:
            print("Response is not in JSON format. Using raw response.")
            analysis_result = analysis_response

        # Append the analysis result to the conversation
        conversation.append({
            "role": "system",
            "content": "Conversation Analysis",
            "analysis": analysis_result
        })

        # Write the updated conversation back to the JSON file
        with open(output_file, 'w') as f:
            json.dump(conversation, f, indent=4)

        print(f"Analysis appended to {output_file}")
        
    except Exception as e:
        print(f"Error in analyze_conversation: {str(e)}")
        print("Traceback:")
        traceback.print_exc()