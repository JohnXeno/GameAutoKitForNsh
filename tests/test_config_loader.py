import unittest
import json
import os
import sys
from unittest.mock import patch

# Adjust path to import from the root directory
# This assumes 'tests' is a top-level directory and the script is run from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_loader import load_workflow_config

class TestConfigLoader(unittest.TestCase):

    def setUp(self):
        """Set up temporary files and directories for tests."""
        self.test_files_dir = "test_temp_configs"
        os.makedirs(self.test_files_dir, exist_ok=True)

        self.valid_config_path = os.path.join(self.test_files_dir, "valid.json")
        self.invalid_json_path = os.path.join(self.test_files_dir, "invalid.json")
        self.empty_file_path = os.path.join(self.test_files_dir, "empty.json")
        self.empty_json_object_path = os.path.join(self.test_files_dir, "empty_object.json")
        self.non_existent_file_path = "non_existent_file.json" # This file should not exist

        # Create dummy files
        self.valid_config_data = {"name": "Test Workflow", "steps": []}
        with open(self.valid_config_path, 'w') as f:
            json.dump(self.valid_config_data, f)

        with open(self.invalid_json_path, 'w') as f:
            f.write('{"name": "Test Workflow", "steps": [') # Malformed JSON

        with open(self.empty_file_path, 'w') as f:
            pass  # Create an empty file

        with open(self.empty_json_object_path, 'w') as f:
            json.dump({}, f) # Empty JSON object

    def tearDown(self):
        """Clean up temporary files and directories."""
        if os.path.exists(self.valid_config_path):
            os.remove(self.valid_config_path)
        if os.path.exists(self.invalid_json_path):
            os.remove(self.invalid_json_path)
        if os.path.exists(self.empty_file_path):
            os.remove(self.empty_file_path)
        if os.path.exists(self.empty_json_object_path):
            os.remove(self.empty_json_object_path)
        
        if os.path.exists(self.test_files_dir):
            # Check if directory is empty before trying to remove it
            if not os.listdir(self.test_files_dir):
                 os.rmdir(self.test_files_dir)
            else:
                # This case should ideally not happen if cleanup is correct
                print(f"Warning: Directory {self.test_files_dir} was not empty during tearDown.")


    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config = load_workflow_config(self.valid_config_path)
        self.assertIsNotNone(config, "Loading a valid config should not return None.")
        self.assertEqual(config["name"], "Test Workflow", "Config name does not match.")
        self.assertEqual(config, self.valid_config_data, "Loaded config data does not match expected data.")

    @patch('config_loader.logger.error')
    def test_load_non_existent_file(self, mock_log_error):
        """Test loading a non-existent configuration file."""
        config = load_workflow_config(self.non_existent_file_path)
        self.assertIsNone(config, "Loading a non-existent file should return None.")
        mock_log_error.assert_called_once() # Check if logger.error was called

    @patch('config_loader.logger.error')
    def test_load_invalid_json(self, mock_log_error):
        """Test loading a file with invalid JSON content."""
        config = load_workflow_config(self.invalid_json_path)
        self.assertIsNone(config, "Loading an invalid JSON file should return None.")
        mock_log_error.assert_called_once()

    @patch('config_loader.logger.error')
    def test_load_empty_file(self, mock_log_error):
        """Test loading an empty file (which is not valid JSON)."""
        config = load_workflow_config(self.empty_file_path)
        self.assertIsNone(config, "Loading an empty file should return None.")
        mock_log_error.assert_called_once()

    def test_load_empty_json_object(self):
        """Test loading a file containing an empty JSON object."""
        config = load_workflow_config(self.empty_json_object_path)
        self.assertIsNotNone(config, "Loading an empty JSON object should not return None.")
        self.assertEqual(config, {}, "Config should be an empty dictionary.")

if __name__ == '__main__':
    unittest.main()
