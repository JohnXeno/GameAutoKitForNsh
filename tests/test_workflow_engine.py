import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock, call

# Adjust path to import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from workflow_engine import WorkflowEngine

# Disable logging for most tests to keep output clean, can be enabled for specific tests
# logging.disable(logging.CRITICAL)

class TestWorkflowEngineResolvers(unittest.TestCase):
    """Tests for the _resolve_parameters method of WorkflowEngine."""

    def setUp(self):
        # A minimal config for initializing WorkflowEngine, not used by _resolve_parameters directly
        self.mock_config_path = "dummy_config.json"

    def test_resolve_parameters_no_vars(self):
        """Test resolving parameters with no placeholders and empty engine variables."""
        engine = WorkflowEngine(self.mock_config_path) # engine.variables will be {}
        engine.workflow_config = {"variables": {}} # Ensure variables are empty for this test
        
        params = {"text": "Hello World", "value": 123}
        resolved_params = engine._resolve_parameters(params)
        self.assertEqual(resolved_params, params)

    def test_resolve_parameters_with_vars(self):
        """Test resolving parameters with simple variable placeholders."""
        engine = WorkflowEngine(self.mock_config_path)
        engine.variables = {"name": "TestUser", "system_id": "SystemA"}
        
        params = {
            "greeting": "Hello {{variables.name}}",
            "target": "{{variables.system_id}}",
            "static": "Value"
        }
        expected = {
            "greeting": "Hello TestUser",
            "target": "SystemA",
            "static": "Value"
        }
        resolved_params = engine._resolve_parameters(params)
        self.assertEqual(resolved_params, expected)

    def test_resolve_parameters_nested(self):
        """Test resolving parameters with nested structures containing variables."""
        engine = WorkflowEngine(self.mock_config_path)
        engine.variables = {"key": "value_for_key", "outer_key": "outer_value"}
        
        params = {
            "data": {
                "value": "{{variables.key}}",
                "config": {
                    "setting": "{{variables.outer_key}}"
                }
            },
            "top_level": "{{variables.outer_key}}"
        }
        expected = {
            "data": {
                "value": "value_for_key",
                "config": {
                    "setting": "outer_value"
                }
            },
            "top_level": "outer_value"
        }
        resolved_params = engine._resolve_parameters(params)
        self.assertEqual(resolved_params, expected)

    def test_resolve_parameters_undefined_var(self):
        """Test resolving parameters when a variable placeholder is undefined."""
        engine = WorkflowEngine(self.mock_config_path)
        engine.variables = {"defined_var": "Exists"}
        
        params = {
            "message": "Value is {{variables.undefined_var}}",
            "known": "{{variables.defined_var}}"
        }
        # Current implementation leaves undefined variables as is
        expected = {
            "message": "Value is {{variables.undefined_var}}",
            "known": "Exists"
        }
        resolved_params = engine._resolve_parameters(params)
        self.assertEqual(resolved_params, expected)

    def test_resolve_parameters_list_with_vars(self):
        """Test resolving parameters where a list contains variable placeholders."""
        engine = WorkflowEngine(self.mock_config_path)
        engine.variables = {"item1": "FirstItem", "item2": "SecondItem"}
        
        params = {
            "items": [
                "{{variables.item1}}",
                "StaticValue",
                {"detail": "{{variables.item2}}"},
                "{{variables.undefined_var}}"
            ]
        }
        expected = {
            "items": [
                "FirstItem",
                "StaticValue",
                {"detail": "SecondItem"},
                "{{variables.undefined_var}}"
            ]
        }
        resolved_params = engine._resolve_parameters(params)
        self.assertEqual(resolved_params, expected)

    def test_resolve_parameters_with_local_vars(self):
        """Test resolving parameters with local variables taking precedence."""
        engine = WorkflowEngine(self.mock_config_path)
        engine.variables = {"name": "GlobalName", "global_only": "GlobalValue"}
        local_vars = {"name": "LocalName", "local_only": "LocalValue"}

        params = {
            "resolved_name": "{{variables.name}}", # Should be global
            "resolved_local_name": "{{local_vars.name}}", # Should be local
            "global_val": "{{variables.global_only}}",
            "local_val": "{{local_vars.local_only}}"
        }
        expected = {
            "resolved_name": "GlobalName",
            "resolved_local_name": "LocalName",
            "global_val": "GlobalValue",
            "local_val": "LocalValue"
        }
        resolved_params = engine._resolve_parameters(params, local_vars=local_vars)
        self.assertEqual(resolved_params, expected)


# Test class for WorkflowEngine's run method and action handling
@patch('workflow_engine.time.sleep') # Patch time.sleep globally for all run tests
@patch('workflow_engine.input_simulation')
@patch('workflow_engine.screen_interaction')
@patch('workflow_engine.load_workflow_config')
class TestWorkflowEngineRun(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        # Disable widespread logging from the engine during tests
        # You can enable it for specific tests if you want to check log output
        logging.disable(logging.CRITICAL)
        self.workflow_path = "test_workflow.json" # Dummy path

    def tearDown(self):
        """Re-enable logging after tests."""
        logging.disable(logging.NOTSET)

    def test_run_simple_workflow_debug_print(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test a simple workflow with a single debug_print action."""
        mock_load_config.return_value = {
            "name": "Test Debug Print",
            "start_step_id": "step1",
            "variables": {},
            "steps": [{
                "id": "step1",
                "action": "debug_print",
                "parameters": {"message": "Hello Workflow"},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        
        with patch.object(engine.logger, 'info') as mock_logger_info, \
             patch('builtins.print') as mock_print: # If debug_print also uses print
            engine.run()
        
        # Check that debug_print's message was logged or printed
        # Based on current implementation, debug_print uses both print and logger.info
        mock_print.assert_any_call("DEBUG_PRINT (Step: step1): Hello Workflow")
        mock_logger_info.assert_any_call("Executed debug_print action for step '%s' with message: %s", "step1", "Hello Workflow")


    def test_run_set_variable_and_resolve(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test set_variable action and then using that variable."""
        mock_load_config.return_value = {
            "name": "Test Set Variable",
            "start_step_id": "step1_set",
            "variables": {"initial_var": "initial_value"},
            "steps": [
                {
                    "id": "step1_set",
                    "action": "set_variable",
                    "parameters": {"variable_name": "my_var", "value": "Set In Step1: {{variables.initial_var}}"},
                    "on_success": "step2_print"
                },
                {
                    "id": "step2_print",
                    "action": "debug_print",
                    "parameters": {"message": "My variable is: {{variables.my_var}}"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch.object(engine.logger, 'info') as mock_logger_info, \
             patch('builtins.print') as mock_print:
            engine.run()

        self.assertEqual(engine.variables.get("my_var"), "Set In Step1: initial_value")
        mock_print.assert_any_call("DEBUG_PRINT (Step: step2_print): My variable is: Set In Step1: initial_value")


    def test_run_wait_action(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test the wait action."""
        mock_load_config.return_value = {
            "name": "Test Wait",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "wait",
                "parameters": {"seconds": 2.5},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        engine.run()
        mock_sleep.assert_called_once_with(2.5)


    def test_run_on_success_branching(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test on_success branching to a different step."""
        mock_load_config.return_value = {
            "name": "Test Success Branch",
            "start_step_id": "step_a",
            "steps": [
                {
                    "id": "step_a",
                    "action": "debug_print",
                    "parameters": {"message": "Step A"},
                    "on_success": "step_b"
                },
                {
                    "id": "step_b",
                    "action": "debug_print",
                    "parameters": {"message": "Step B"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch('builtins.print') as mock_print:
            engine.run()
        
        mock_print.assert_any_call("DEBUG_PRINT (Step: step_a): Step A")
        mock_print.assert_any_call("DEBUG_PRINT (Step: step_b): Step B")
        

    def test_run_on_failure_branching(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test on_failure branching when an action fails."""
        mock_screen_ia.wait_for_image.return_value = None # Simulate image not found -> failure
        mock_load_config.return_value = {
            "name": "Test Failure Branch",
            "start_step_id": "step_find",
            "steps": [
                {
                    "id": "step_find",
                    "action": "find_image_and_click",
                    "parameters": {"image_path": "nonexistent.png"},
                    "on_success": "step_success_path",
                    "on_failure": "step_failure_path"
                },
                {
                    "id": "step_success_path",
                    "action": "debug_print",
                    "parameters": {"message": "Should not reach here"},
                    "on_success": "exit"
                },
                {
                    "id": "step_failure_path",
                    "action": "debug_print",
                    "parameters": {"message": "Reached failure path correctly"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch('builtins.print') as mock_print:
            engine.run()
        
        mock_screen_ia.wait_for_image.assert_called_once()
        mock_print.assert_any_call("DEBUG_PRINT (Step: step_failure_path): Reached failure path correctly")
        
        # Check that step_success_path was not called
        success_message_call = call("DEBUG_PRINT (Step: step_success_path): Should not reach here")
        self.assertNotIn(success_message_call, mock_print.call_args_list)


    def test_run_find_image_and_click_success(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test find_image_and_click action successfully finds and clicks."""
        mock_screen_ia.wait_for_image.return_value = (100, 200) # Simulate image found
        mock_load_config.return_value = {
            "name": "Test Find and Click Success",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "find_image_and_click",
                "parameters": {"image_path": "found.png", "button": "right", "offset_x": 5, "offset_y": -10},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        engine.run()
        
        mock_screen_ia.wait_for_image.assert_called_once_with("found.png", timeout=10, confidence_threshold=0.9) # Default timeout/confidence
        mock_input_sim.mouse_click.assert_called_once_with(x=105, y=190, button="right")


    def test_run_type_text_action(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test type_text action."""
        mock_load_config.return_value = {
            "name": "Test Type Text",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "type_text",
                "parameters": {"text": "Hello Automation"},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        engine.run()
        mock_input_sim.type_string.assert_called_once_with("Hello Automation")

    def test_run_press_key_action(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test press_key action."""
        mock_load_config.return_value = {
            "name": "Test Press Key",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "press_key",
                "parameters": {"key": "enter"},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        engine.run()
        mock_input_sim.key_press.assert_called_once_with("enter")

    def test_run_mouse_click_coordinates_action(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test mouse_click_coordinates action."""
        mock_load_config.return_value = {
            "name": "Test Click Coords",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "mouse_click_coordinates",
                "parameters": {"x": 55, "y": 77, "button": "middle"},
                "on_success": "exit"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        engine.run()
        mock_input_sim.mouse_click.assert_called_once_with(x=55, y=77, button="middle")

    def test_run_unknown_action(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test workflow with an unknown action, expects on_failure or exit."""
        mock_load_config.return_value = {
            "name": "Test Unknown Action",
            "start_step_id": "step1",
            "steps": [
                {
                    "id": "step1",
                    "action": "non_existent_action",
                    "parameters": {},
                    "on_success": "step_success",
                    "on_failure": "step_failure"
                },
                {
                    "id": "step_success",
                    "action": "debug_print",
                    "parameters": {"message": "Should not be called"},
                    "on_success": "exit"
                },
                {
                    "id": "step_failure",
                    "action": "debug_print",
                    "parameters": {"message": "Failure path for unknown action"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch.object(engine.logger, 'error') as mock_logger_error, \
             patch('builtins.print') as mock_print:
            engine.run()
        
        mock_logger_error.assert_any_call("Unknown action '%s' in step '%s'.", "non_existent_action", "step1")
        mock_print.assert_any_call("DEBUG_PRINT (Step: step_failure): Failure path for unknown action")


    def test_run_workflow_config_load_fails(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test engine behavior when workflow config loading fails."""
        mock_load_config.return_value = None # Simulate load_workflow_config returning None
        
        # Patch the logger for WorkflowEngine instance specifically for __init__
        # This is a bit tricky because the logger is initialized in __init__
        # So we patch the logger that WorkflowEngine class will use
        with patch('workflow_engine.logging.getLogger') as mock_get_logger:
            mock_engine_logger = MagicMock()
            mock_get_logger.return_value = mock_engine_logger
            
            engine = WorkflowEngine(self.workflow_path)
            # engine.workflow_config should be None
            self.assertIsNone(engine.workflow_config)
            # Check that an error was logged during initialization
            mock_engine_logger.error.assert_called_with(
                "Workflow configuration could not be loaded from '%s'. Engine initialization failed.", 
                self.workflow_path
            )

            # Now, try to run the engine
            # We also need to ensure the run method's own logger doesn't mask the init logger
            engine.logger = mock_engine_logger # Assign the same mock logger to the instance
            engine.run()
            
            # Check that run method logged an error and exited gracefully
            mock_engine_logger.error.assert_any_call("Workflow configuration is not loaded or contains no steps. Cannot run workflow.")


    def test_run_step_not_found(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test behavior when a step ID in on_success/on_failure is not found."""
        mock_load_config.return_value = {
            "name": "Test Step Not Found",
            "start_step_id": "step1",
            "steps": [{
                "id": "step1",
                "action": "debug_print",
                "parameters": {"message": "First step"},
                "on_success": "non_existent_step_id"
            }]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch.object(engine.logger, 'error') as mock_logger_error:
            engine.run()
        
        mock_logger_error.assert_called_with("Step with ID '%s' not found in workflow. Aborting.", "non_existent_step_id")


    def test_run_default_on_success_next_in_list(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test default on_success behavior (proceed to next step in list)."""
        mock_load_config.return_value = {
            "name": "Test Default On Success",
            "start_step_id": "step1",
            "steps": [
                {
                    "id": "step1",
                    "action": "debug_print",
                    "parameters": {"message": "This is Step 1"}
                    # No on_success, should go to step2
                },
                {
                    "id": "step2",
                    "action": "debug_print",
                    "parameters": {"message": "This is Step 2"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch('builtins.print') as mock_print:
            engine.run()
        
        mock_print.assert_any_call("DEBUG_PRINT (Step: step1): This is Step 1")
        mock_print.assert_any_call("DEBUG_PRINT (Step: step2): This is Step 2")


    def test_run_default_on_failure_exit(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test default on_failure behavior (exit workflow)."""
        mock_screen_ia.wait_for_image.return_value = None # Cause failure
        mock_load_config.return_value = {
            "name": "Test Default On Failure",
            "start_step_id": "step1",
            "steps": [
                {
                    "id": "step1",
                    "action": "find_image_and_click",
                    "parameters": {"image_path": "fail.png"}
                    # No on_failure, should exit
                },
                {
                    "id": "step2_should_not_run",
                    "action": "debug_print",
                    "parameters": {"message": "This step should not execute"},
                    "on_success": "exit"
                }
            ]
        }
        engine = WorkflowEngine(self.workflow_path)
        with patch.object(engine.logger, 'error') as mock_logger_error, \
             patch('builtins.print') as mock_print:
            engine.run()
        
        # Check that the failing step was logged
        mock_logger_error.assert_any_call("Image '%s' not found on screen within %ss for step '%s'.", "fail.png", 10, "step1")
        # Check that the specific message for exiting due to no on_failure is logged
        mock_logger_error.assert_any_call("Step '%s' failed and no 'on_failure' target specified. Exiting.", "step1")
        
        # Verify step2_should_not_run was not executed
        unexpected_call = call("DEBUG_PRINT (Step: step2_should_not_run): This step should not execute")
        self.assertNotIn(unexpected_call, mock_print.call_args_list)


    def test_run_variable_resolution_in_action_params(self, mock_load_config, mock_screen_ia, mock_input_sim, mock_sleep):
        """Test that variables are resolved in action parameters."""
        mock_load_config.return_value = {
            "name": "Test Variable Resolution in Params",
            "start_step_id": "step1",
            "variables": {
                "target_image_file": "actual_image.png",
                "click_button": "left",
                "wait_time": "0.5" # String that needs conversion for 'wait' action
            },
            "steps": [
                {
                    "id": "step1",
                    "action": "find_image_and_click",
                    "parameters": {
                        "image_path": "{{variables.target_image_file}}",
                        "button": "{{variables.click_button}}",
                        "timeout": 5 
                    },
                    "on_success": "step2"
                },
                {
                    "id": "step2",
                    "action": "wait",
                    "parameters": {"seconds": "{{variables.wait_time}}"},
                    "on_success": "exit"
                }
            ]
        }
        mock_screen_ia.wait_for_image.return_value = (10,10) # Allow find_image to succeed

        engine = WorkflowEngine(self.workflow_path)
        engine.run()

        mock_screen_ia.wait_for_image.assert_called_once_with(
            "actual_image.png", 
            timeout=5, # This was literal in config
            confidence_threshold=0.9 # Default
        )
        mock_input_sim.mouse_click.assert_called_once_with(x=10, y=10, button="left")
        mock_sleep.assert_called_once_with(0.5) # Check that string "0.5" was converted to float


if __name__ == '__main__':
    unittest.main()
