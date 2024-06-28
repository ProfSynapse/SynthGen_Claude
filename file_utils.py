# file_utils.py

import os
import PyPDF2

def read_file(file_path):
    """
    Read the content of a file, supporting .md, .txt, and .pdf files.

    Args:
        file_path (str): Path to the file.

    Returns:
        dict: A dictionary containing the filename and content of the file.
    """
    filename = os.path.basename(file_path)
    
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text()
    else:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    
    return {"filename": filename, "content": content}

def load_processed_files(processed_files_file):
    """
    Load the list of processed files from a text file.

    Args:
        processed_files_file (str): Path to the file containing processed files.

    Returns:
        set: Set of processed file paths.
    """
    if os.path.exists(processed_files_file):
        with open(processed_files_file, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_processed_file(processed_files_file, file_path):
    """
    Save a processed file path to the list of processed files.

    Args:
        processed_files_file (str): Path to the file containing processed files.
        file_path (str): Path of the processed file to save.
    """
    with open(processed_files_file, 'a') as f:
        f.write(file_path + '\n')