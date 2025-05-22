import unittest
import os
import sys
import logging
import io # For capturing stderr/stdout
from unittest.mock import patch, MagicMock, call

# Adjust path to import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main module. This will execute main.py's top-level code,
# including its logger setup if __name__ == '__main__' was triggered,
# which we want to avoid in tests.
# Instead, we'll import specific functions or classes if needed,
# or patch things before main.main() is called.
import main # This imports the main.py module

class TestMain(unittest.TestCase):

    # We need to ensure logging is set up for tests that check log messages
    # but also that we can control it per test.
    def setUp(self):
        # Store original sys.argv to restore it later
        self.original_argv = sys.argv
        # It's good practice to reset log handlers if main.py might add them globally
        # For now, we'll rely on patching basicConfig or specific loggers

    def tearDown(self):
        sys.argv = self.original_argv # Restore original sys.argv
        # Ensure no handlers are left on root logger from tests
        # for handler in logging.root.handlers[:]:
        #     logging.root.removeHandler(handler)


    @patch('main.WorkflowEngine')
    @patch('main.sys.exit') # Mock sys.exit to prevent test runner from exiting
    def test_main_run_workflow_success(self, mock_sys_exit, MockWorkflowEngine):
        """Test main.py successfully runs a workflow."""
        # Mock sys.argv
        sys.argv = ['main.py', '--workflow', 'dummy_workflow.json']
        
        mock_engine_instance = MockWorkflowEngine.return_value
        mock_engine_instance.workflow_config = {"name": "mocked_config"} # Simulate successful load
        
        main.main()
        
        MockWorkflowEngine.assert_called_once_with(config_path='dummy_workflow.json')
        mock_engine_instance.run.assert_called_once()
        mock_sys_exit.assert_not_called() # Should not exit if successful

    @patch('main.logging.basicConfig')
    @patch('main.WorkflowEngine')
    @patch('main.sys.exit')
    def test_main_loglevel_debug(self, mock_sys_exit, MockWorkflowEngine, mock_basic_config):
        """Test main.py sets loglevel correctly (e.g., to DEBUG)."""
        sys.argv = ['main.py', '--workflow', 'dummy.json', '--loglevel', 'DEBUG']
        
        mock_engine_instance = MockWorkflowEngine.return_value
        mock_engine_instance.workflow_config = {"name": "mocked_config"}
        
        main.main()
        
        # Check that logging.basicConfig was called
        mock_basic_config.assert_called_once()
        # Check that 'level' was in the kwargs and set to logging.DEBUG
        args, kwargs = mock_basic_config.call_args
        self.assertEqual(kwargs.get('level'), logging.DEBUG)
        mock_sys_exit.assert_not_called()


    @patch('main.argparse.ArgumentParser.print_help') # Mock print_help
    @patch('main.sys.exit') # Mock sys.exit
    @patch('main.logging.getLogger') # To get a handle on the main_logger
    def test_main_missing_workflow_arg(self, mock_get_logger, mock_sys_exit, mock_print_help):
        """Test main.py exits when --workflow argument is missing."""
        sys.argv = ['main.py'] # No --workflow argument
        
        # Mock the logger used in main.py to check its output
        mock_main_logger = MagicMock()
        mock_get_logger.return_value = mock_main_logger

        main.main()
        
        mock_main_logger.error.assert_called_with("Workflow file path must be provided.")
        mock_print_help.assert_called_once() #ArgumentParser's print_help
        mock_sys_exit.assert_called_once_with(1)


    @patch('main.WorkflowEngine')
    @patch('main.sys.exit')
    @patch('main.logging.getLogger') # Patch the logger used in main.py
    def test_main_workflow_load_fails_in_engine(self, mock_get_logger, mock_sys_exit, MockWorkflowEngine):
        """Test main.py handles WorkflowEngine failing to load a config."""
        sys.argv = ['main.py', '--workflow', 'bad_workflow.json']
        
        mock_engine_instance = MockWorkflowEngine.return_value
        mock_engine_instance.workflow_config = None # Simulate engine failing to load config
        
        mock_main_logger = MagicMock()
        mock_get_logger.return_value = mock_main_logger

        main.main()
        
        MockWorkflowEngine.assert_called_once_with(config_path='bad_workflow.json')
        mock_engine_instance.run.assert_not_called()
        
        # Check that the specific error message from main.py is logged
        mock_main_logger.error.assert_called_with(
            f"Failed to initialize WorkflowEngine for 'bad_workflow.json'. Check previous logs for details."
        )
        mock_sys_exit.assert_called_once_with(1)


    @patch('main.WorkflowEngine')
    @patch('main.sys.exit')
    @patch('main.logging.getLogger')
    def test_main_engine_run_raises_exception(self, mock_get_logger, mock_sys_exit, MockWorkflowEngine):
        """Test main.py handles exceptions raised by engine.run()."""
        sys.argv = ['main.py', '--workflow', 'dummy.json']
        
        mock_engine_instance = MockWorkflowEngine.return_value
        mock_engine_instance.workflow_config = {"name": "mocked_config"}
        test_exception = Exception("Something broke during run")
        mock_engine_instance.run.side_effect = test_exception
        
        mock_main_logger = MagicMock()
        mock_get_logger.return_value = mock_main_logger
        
        main.main()
        
        MockWorkflowEngine.assert_called_once_with(config_path='dummy.json')
        mock_engine_instance.run.assert_called_once()
        
        # Check that the exception was logged
        mock_main_logger.error.assert_called_with(
            f"Exception occurred during workflow execution: {test_exception}",
            exc_info=True
        )
        mock_sys_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
