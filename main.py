# main.py

import os
import shutil
from config import load_config
from conversation import generate_conversation, format_output
from file_utils import read_file, load_processed_files, save_processed_file
from anthropic import exceptions
from datetime import datetime

def process_file(file_path, config, processed_files_file):
    """
    Process a single file and generate conversations.

    Args:
        file_path (str): Path to the file.
        config (dict): Configuration settings.
        processed_files_file (str): File to track processed files.

    Returns:
        list: List of generated conversations.
    """
    # Create the synth_conversations folder if it doesn't exist
    synth_conversations_folder = "synth_conversations"
    os.makedirs(synth_conversations_folder, exist_ok=True)
    
    # Generate a unique output file name based on the current date/time and original filename
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(synth_conversations_folder, f"synthgen_{base_filename}_{current_datetime}.json")
    
    conversations = []
    
    for i in range(config['conversation_generation']['num_conversations']):
        print(f"\nGenerating conversation {i + 1} for file: {file_path}")
        try:
            file_content = read_file(file_path)
            conversation = generate_conversation(
                file_content,
                output_file,
                config,
            )
            if conversation:
                formatted_output = format_output(conversation)
                conversations.append(formatted_output)
                save_processed_file(processed_files_file, file_path)
                print(f"Processed file {file_path} and appended to processed_files.txt")
        except exceptions.APIException as e:
            print(str(e))
            print("Error with Claude API. Please try again later.")
            return conversations
    
    print(f"Finished processing file: {file_path}")
    return conversations

def main():
    """
    The main function to run the script.
    """
    config = load_config('config.yaml')
    processed_files_file = 'processed_files.txt'
    processed_files = load_processed_files(processed_files_file)

    input_folder = config['file_paths']['input_folder']
    output_folder = config['file_paths']['output_folder']
    os.makedirs(output_folder, exist_ok=True)

    print("Starting to process files...")
    
    files_to_process = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith((".md", ".txt", ".pdf")):
                file_path = os.path.join(root, file)
                if file_path in processed_files:
                    print(f"\nSkipping already processed file: {file_path}")
                    continue

                files_to_process.append(file_path)

    # Process files sequentially
    for file_path in files_to_process:
        process_file(file_path, config, processed_files_file)
        
        # Move the processed file to the output folder
        output_path = os.path.join(output_folder, os.path.basename(file_path))
        shutil.move(file_path, output_path)
        print(f"Moved {file_path} to {output_path}")

    print("Script finished.")

if __name__ == "__main__":
    main()