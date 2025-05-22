from config_loader import load_workflow_config
import screen_interaction
import input_simulation
import time
import re
import logging

class WorkflowEngine:
    """
    Manages and executes a series of automated steps defined in a workflow configuration file.
    """

    def __init__(self, config_path):
        """
        Initializes the WorkflowEngine.

        Args:
            config_path (str): The path to the workflow configuration JSON file.
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__) # Get logger instance
        self.workflow_config = load_workflow_config(config_path)
        
        if self.workflow_config:
            self.variables = self.workflow_config.get('variables', {}).copy()
            # Determine the first step ID
            if 'steps' in self.workflow_config and len(self.workflow_config['steps']) > 0:
                # Try to get a designated start_step_id, otherwise default to the first step's id
                self.current_step_id = self.workflow_config.get('start_step_id', self.workflow_config['steps'][0].get('id'))
            else:
                self.current_step_id = None
            self.logger.info("Workflow configuration loaded successfully from '%s'.", config_path)
        else:
            self.variables = {}
            self.current_step_id = None
            self.logger.error("Workflow configuration could not be loaded from '%s'. Engine initialization failed.", config_path)

    def _resolve_parameters(self, params, local_vars=None):
        """
        Resolves variables in parameter values.
        Looks for {{variables.var_name}} or {{local_vars.var_name}}.

        Args:
            params (dict): The dictionary of parameters for a step.
            local_vars (dict, optional): A dictionary of local variables for the current scope.

        Returns:
            dict: The dictionary with resolved parameters.
        """
        if not isinstance(params, dict):
            return params # Return as is if not a dictionary

        resolved_params = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Resolve self.variables
                value = re.sub(r"{{\s*variables\.(\w+)\s*}}", 
                               lambda m: str(self.variables.get(m.group(1), m.group(0))), 
                               value)
                # Resolve local_vars if provided
                if local_vars:
                    value = re.sub(r"{{\s*local_vars\.(\w+)\s*}}",
                                   lambda m: str(local_vars.get(m.group(1), m.group(0))),
                                   value)
            elif isinstance(value, dict): # Recursively resolve nested dictionaries
                value = self._resolve_parameters(value, local_vars)
            elif isinstance(value, list): # Recursively resolve lists
                value = [self._resolve_parameters(item, local_vars) if isinstance(item, dict) else item for item in value]

            resolved_params[key] = value
        return resolved_params

    def run(self):
        """
        Executes the loaded workflow.
        """
        if not self.workflow_config or 'steps' not in self.workflow_config or not self.workflow_config['steps']:
            self.logger.error("Workflow configuration is not loaded or contains no steps. Cannot run workflow.")
            return

        if not self.current_step_id:
            # Attempt to find the first step again, or a designated start_step_id
            self.current_step_id = self.workflow_config.get('start_step_id')
            if not self.current_step_id and self.workflow_config['steps']:
                 self.current_step_id = self.workflow_config['steps'][0].get('id')
            
            if not self.current_step_id:
                self.logger.error("No starting step ID found in the workflow. Cannot run workflow.")
                return
        
        self.logger.info("Starting workflow execution. Initial step ID: %s", self.current_step_id)

        while self.current_step_id and self.current_step_id != "exit":
            current_step = next((step for step in self.workflow_config['steps'] if step['id'] == self.current_step_id), None)

            if not current_step:
                self.logger.error("Step with ID '%s' not found in workflow. Aborting.", self.current_step_id)
                break

            description = current_step.get('description', 'No description')
            self.logger.info("Executing step: ID='%s', Description='%s'", self.current_step_id, description)
            
            local_vars_for_step = {} # If we introduce step-specific local vars later
            resolved_params = self._resolve_parameters(current_step.get('parameters', {}), local_vars_for_step)
            self.logger.debug("Resolved parameters for step '%s': %s", self.current_step_id, resolved_params)

            # params = self._resolve_parameters(current_step.get('parameters', {})) # Old line
            params = resolved_params # Use the new variable that holds resolved params
            action = current_step.get('action')
            step_succeeded = False # Default to failure

            try:
                if action == "find_image_and_click":
                    image_path_param = params.get('image_path') 
                    if not image_path_param:
                        self.logger.error("Step '%s': 'image_path' parameter is required for 'find_image_and_click'.", self.current_step_id)
                    else:
                        # image_path is already resolved by the initial call to _resolve_parameters for the step.
                        # No need for: local_vars = {} and str(self._resolve_parameters({"path": image_path_param}, local_vars).get("path", image_path_param))
                        image_path = str(image_path_param) # Ensure it's a string

                        timeout = float(params.get('timeout', 10))
                        confidence = float(params.get('confidence_threshold', 0.9))
                        button = str(params.get('button', 'left'))
                        offset_x = int(params.get('offset_x', 0))
                        offset_y = int(params.get('offset_y', 0))
                        
                        self.logger.debug("Attempting to find image '%s' (timeout=%s, confidence=%s)", image_path, timeout, confidence)
                        location = screen_interaction.wait_for_image(image_path, timeout=timeout, confidence_threshold=confidence)
                        if location:
                            click_x = location[0] + offset_x
                            click_y = location[1] + offset_y
                            self.logger.info("Image '%s' found at %s. Clicking at (%s, %s).", image_path, location, click_x, click_y)
                            input_simulation.mouse_click(x=click_x, y=click_y, button=button)
                            step_succeeded = True
                        else:
                            self.logger.error("Image '%s' not found on screen within %ss for step '%s'.", image_path, timeout, self.current_step_id)
                            step_succeeded = False
                
                elif action == "type_text":
                    text_to_type = params.get('text')
                    if text_to_type is None: 
                         self.logger.error("Step '%s': 'text' parameter is required for 'type_text'.", self.current_step_id)
                    else:
                        self.logger.debug("Typing text: '%s'", text_to_type)
                        input_simulation.type_string(str(text_to_type)) 
                        step_succeeded = True

                elif action == "press_key":
                    key_to_press = params.get('key')
                    if not key_to_press:
                        self.logger.error("Step '%s': 'key' parameter is required for 'press_key'.", self.current_step_id)
                    else:
                        self.logger.debug("Pressing key: '%s'", key_to_press)
                        input_simulation.key_press(str(key_to_press))
                        step_succeeded = True

                elif action == "mouse_click_coordinates":
                    x = params.get('x')
                    y = params.get('y')
                    if x is None or y is None:
                        self.logger.error("Step '%s': 'x' and 'y' parameters are required for 'mouse_click_coordinates'.", self.current_step_id)
                    else:
                        button = str(params.get('button', 'left')) 
                        self.logger.debug("Clicking at coordinates: (x=%s, y=%s), button=%s", x, y, button)
                        input_simulation.mouse_click(x=int(x), y=int(y), button=button) 
                        step_succeeded = True
                
                elif action == "wait":
                    seconds = params.get('seconds')
                    if seconds is None:
                         self.logger.error("Step '%s': 'seconds' parameter is required for 'wait'.", self.current_step_id)
                    else:
                        self.logger.debug("Waiting for %s seconds.", seconds)
                        time.sleep(float(seconds)) 
                        step_succeeded = True

                elif action == "debug_print":
                    message = params.get('message', '') 
                    print(f"DEBUG_PRINT (Step: {self.current_step_id}): {message}") # Keep user-facing print
                    self.logger.info("Executed debug_print action for step '%s' with message: %s", self.current_step_id, message)
                    step_succeeded = True
                
                elif action == "set_variable":
                    original_step_params = current_step.get('parameters', {}) # Get unresolved params for var name
                    variable_name_literal = original_step_params.get('variable_name')
                    
                    if not variable_name_literal:
                        self.logger.error("Step '%s': 'variable_name' key is missing in parameters for 'set_variable'.", self.current_step_id)
                    elif "{{" in variable_name_literal or "}}" in variable_name_literal:
                         self.logger.error("Step '%s': 'variable_name' ('%s') in 'set_variable' cannot be a variable placeholder itself. It must be a literal string.", self.current_step_id, variable_name_literal)
                    else:
                        var_value = params.get('value') # This 'value' is from already resolved_params
                        self.variables[variable_name_literal] = var_value
                        self.logger.info("Variable '%s' set to '%s'. Current variables: %s", variable_name_literal, var_value, self.variables)
                        step_succeeded = True
                
                else:
                    self.logger.error("Unknown action '%s' in step '%s'.", action, self.current_step_id)
                    step_succeeded = False
            
            except Exception as e:
                self.logger.error("An unexpected error occurred during action '%s' in step '%s': %s", action, self.current_step_id, e, exc_info=True)
                step_succeeded = False

            if step_succeeded:
                self.logger.info("Step '%s' executed successfully.", self.current_step_id)
                next_step_id = current_step.get('on_success')
                if next_step_id is None: # If on_success is not defined, go to next step by order if possible
                    current_index = self.workflow_config['steps'].index(current_step)
                    if current_index + 1 < len(self.workflow_config['steps']):
                        self.current_step_id = self.workflow_config['steps'][current_index + 1].get('id')
                    else:
                        self.current_step_id = "exit" # Last step
                else:
                    self.current_step_id = next_step_id
            else:
                next_step_id = current_step.get('on_failure')
                if next_step_id is None: 
                    self.logger.error("Step '%s' failed and no 'on_failure' target specified. Exiting.", self.current_step_id)
                    self.current_step_id = "exit"
                else:
                    self.logger.info("Step '%s' failed. Transitioning to 'on_failure' step: '%s'", self.current_step_id, next_step_id)
                    self.current_step_id = next_step_id
            
            # Optional: Add a small delay between steps
            # time.sleep(0.1) 

        if self.current_step_id == "exit":
            self.logger.info("Workflow execution finished (reached 'exit' step).")
        elif not self.current_step_id: # Should ideally be caught by other conditions but as a fallback
             self.logger.info("Workflow execution stopped due to missing next step ID or end of defined path.")


if __name__ == '__main__':
    # Create dummy config files for testing
    # Valid config
    valid_config_content = {
        "name": "Test Workflow",
        "variables": {"site": "example.com", "search_term": "testing"},
        "start_step_id": "step1",
        "steps": [
            {
                "id": "step1",
                "description": "Open browser and go to site",
                "action": "debug_print",
                "parameters": {"message": "Navigating to {{variables.site}} to search for {{variables.search_term}}"},
                "on_success": "step2"
            },
            {
                "id": "step2",
                "description": "Type search term",
                "action": "type_text",
                "parameters": {"text": "{{variables.search_term}}"},
                "on_success": "step3"
            },
            {
                "id": "step3",
                "description": "Wait a bit",
                "action": "wait",
                "parameters": {"seconds": 0.1},
                "on_success": "step4_set_var"
            },
            {
                "id": "step4_set_var",
                "description": "Set a new variable",
                "action": "set_variable",
                "parameters": {"variable_name": "status", "value": "completed_step4"},
                "on_success": "step5_print_var"
            },
            {
                "id": "step5_print_var",
                "description": "Print the new variable",
                "action": "debug_print",
                "parameters": {"message": "Status is: {{variables.status}}"},
                "on_success": "exit"
            }
        ]
    }
    with open("test_workflow.json", "w") as f:
        import json
        json.dump(valid_config_content, f, indent=4)

    # Config with missing steps
    broken_config_content = {"name": "Broken Workflow", "steps": []}
    with open("broken_workflow.json", "w") as f:
        import json
        json.dump(broken_config_content, f, indent=4)

    print("--- Testing WorkflowEngine with a valid workflow ---")
    engine_valid = WorkflowEngine("test_workflow.json")
    # engine_valid.run() # Run will be completed in next steps

    print("\n--- Testing WorkflowEngine with a non-existent config file ---")
    engine_non_existent = WorkflowEngine("non_existent.json")
    # engine_non_existent.run()

    print("\n--- Testing WorkflowEngine with a broken/empty workflow ---")
    engine_broken = WorkflowEngine("broken_workflow.json")
    # engine_broken.run()
    
    print("\n--- Testing _resolve_parameters ---")
    if engine_valid.workflow_config: # Ensure config loaded
        test_params = {"url": "http://{{variables.site}}", "query": "{{variables.search_term}}", "fixed": "value", "nested": {"key": "{{variables.site}}"}}
        resolved = engine_valid._resolve_parameters(test_params)
        print(f"Original params: {test_params}")
        print(f"Resolved params: {resolved}")
        expected_resolved = {'url': 'http://example.com', 'query': 'testing', 'fixed': 'value', 'nested': {'key': 'example.com'}}
        assert resolved == expected_resolved, f"Expected {expected_resolved}, but got {resolved}"

        test_params_local = {"url": "http://{{local_vars.host}}", "port": "{{local_vars.port}}"}
        local_vars_test = {"host": "localhost", "port": "8080"}
        resolved_local = engine_valid._resolve_parameters(test_params_local, local_vars=local_vars_test)
        print(f"Original params (local): {test_params_local}")
        print(f"Resolved params (local): {resolved_local}")
        expected_resolved_local = {'url': 'http://localhost', 'port': '8080'}
        assert resolved_local == expected_resolved_local, f"Expected {expected_resolved_local}, but got {resolved_local}"

    # Clean up
    import os
    # os.remove("test_workflow.json") # Will be used by main.py later, keep for now
    os.remove("broken_workflow.json")

    # The __main__ block is primarily for isolated testing of WorkflowEngine.
    # Full logging setup will be in main.py. For direct tests here,
    # we can add a basic config if needed, or rely on main.py to run this.
    # For now, let's assume that if this __main__ is run directly,
    # we want to see the log messages, so we'll add a simple basicConfig.
    if not logging.getLogger().hasHandlers(): # Avoid reconfiguring if already done (e.g. by main.py)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger_main_test = logging.getLogger(__name__ + "_test")


    logger_main_test.info("--- Testing WorkflowEngine action handling with a dedicated 'set_variable' and 'debug_print' workflow ---")
    
    # Create a specific workflow for testing set_variable and variable resolution
    test_set_var_config = {
        "name": "Set Variable and Debug Test Workflow",
        "variables": {"initial_global_var": "global_start_value", "path_template": "/images/{{variables.image_name}}.png"},
        "start_step_id": "step1_set_initial",
        "steps": [
            {
                "id": "step1_set_initial",
                "description": "Set an initial variable",
                "action": "set_variable",
                "parameters": {"variable_name": "loop_counter", "value": 0},
                "on_success": "step2_debug_print"
            },
            {
                "id": "step2_debug_print",
                "description": "Print initial variables",
                "action": "debug_print", # This will still print to console
                "parameters": {"message": "Initial counter: {{variables.loop_counter}}. Global: {{variables.initial_global_var}}"},
                "on_success": "step3_set_image_name"
            },
            {
                "id": "step3_set_image_name",
                "description": "Set image_name variable",
                "action": "set_variable",
                "parameters": {"variable_name": "image_name", "value": "icon_play"},
                "on_success": "step4_print_image_path"
            },
            {
                "id": "step4_print_image_path",
                "description": "Print the resolved image path",
                "action": "debug_print",
                "parameters": {"message": "Image path will be: {{variables.path_template}}"},
                "on_success": "step5_check_fail_condition" 
            },
            {
                "id": "step5_check_fail_condition",
                "description": "Test on_failure by missing a parameter",
                "action": "wait", 
                "parameters": {}, # 'seconds' parameter is missing -> error
                "on_success": "exit",
                "on_failure": "step6_failure_handler"
            },
            {
                "id": "step6_failure_handler",
                "description": "Handle the failure",
                "action": "debug_print",
                "parameters": {"message": "Successfully handled step5's failure. Current counter: {{variables.loop_counter}}"},
                "on_success": "exit"
            }
        ]
    }
    with open("test_set_var_workflow.json", "w") as f:
        import json
        json.dump(test_set_var_config, f, indent=4)
    
    logger_main_test.info("Running set_variable and debug_print test workflow...")
    engine_test = WorkflowEngine("test_set_var_workflow.json") # Logger will be configured here
    
    if engine_test.workflow_config:
      engine_test.run()
      # Assertions to verify correct execution
      assert engine_test.variables.get("loop_counter") == 0, \
          f"Variable 'loop_counter' expected 0, got: {engine_test.variables.get('loop_counter')}"
      assert engine_test.variables.get("initial_global_var") == "global_start_value", "Global variable not preserved."
      assert engine_test.variables.get("image_name") == "icon_play", "image_name was not set correctly."
      logger_main_test.info("set_variable and debug_print test workflow completed. Check output for debug messages and failure handling.")
    else:
      logger_main_test.error("Failed to load set_variable test workflow.")

    import os
    os.remove("test_set_var_workflow.json")
    # os.remove("test_workflow.json") # Keep this for the main.py task

    logger_main_test.info("WorkflowEngine logging integration complete. Further testing with main.py's logger setup.")
