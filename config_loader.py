import json
import logging

logger = logging.getLogger(__name__)

def load_workflow_config(file_path):
    """
    Loads a workflow configuration from a JSON file.

    Args:
        file_path (str): The path to the JSON configuration file.

    Returns:
        dict: A Python dictionary representing the workflow configuration, 
              or None if an error occurs during loading or parsing.

    Raises:
        (Prints an error message and returns None for):
        FileNotFoundError: If the specified file_path does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        logger.info("Configuration file '%s' loaded successfully.", file_path)
        return config_data
    except FileNotFoundError:
        logger.error("Configuration file not found at '%s'.", file_path)
        return None
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON format in configuration file '%s'. Details: %s", file_path, e)
        return None

if __name__ == '__main__':
    # Basic logging setup for standalone testing of this module
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Example usage (optional, for testing)
    # Create a dummy config file for testing
    dummy_config_valid = {"name": "Test Workflow", "steps": [{"action": "click", "x": 100, "y": 200}]}
    with open("dummy_valid_config.json", "w") as f:
        json.dump(dummy_config_valid, f)

    dummy_config_invalid_json = "This is not valid JSON"
    with open("dummy_invalid_config.json", "w") as f:
        f.write(dummy_config_invalid_json)

    logger.info("--- Testing config_loader with a valid config file: ---")
    config = load_workflow_config("dummy_valid_config.json")
    if config:
        logger.info("Config loaded successfully: %s", config)

    logger.info("--- Testing config_loader with a non-existent file: ---")
    config_non_existent = load_workflow_config("non_existent_config.json")
    if config_non_existent is None:
        logger.info("Handled non-existent file correctly (returned None).")

    logger.info("--- Testing config_loader with an invalid JSON file: ---")
    config_invalid = load_workflow_config("dummy_invalid_config.json")
    if config_invalid is None:
        logger.info("Handled invalid JSON correctly (returned None).")
    
    # Clean up dummy files
    import os
    os.remove("dummy_valid_config.json")
    os.remove("dummy_invalid_config.json")
    
    logger.info("config_loader.py logging integration complete.")
