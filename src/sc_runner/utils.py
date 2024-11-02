# utils.py
import json
import logging

def load_json(file_path: str) -> dict:
    """
    Loads a JSON file and returns its contents.

    Args:
        file_path (str): Path to the JSON file.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        logging.info(f"Loaded JSON data from {file_path}")
        return data
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        raise
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}.")
        raise
