# Python UI Automation Framework

## Overview

This framework provides a way to automate user interface (UI) actions on a computer by simulating human interaction. It uses image recognition to find elements on the screen and then simulates mouse and keyboard actions on these elements. The automation sequences are defined in configurable JSON workflow files, allowing for flexible and reusable automation scripts.

## Features

*   **Image Recognition**: Locates specific images (templates) on the screen to identify UI elements.
*   **Mouse and Keyboard Simulation**: Performs actions like clicking, typing, moving the mouse, and pressing keys.
*   **Configurable Workflows**: Automation steps are defined in easy-to-understand JSON files, allowing for complex sequences and conditional logic.
*   **Variable Support**: Workflows can define and use variables, allowing for dynamic data handling within automation tasks.
*   **Logging**: Comprehensive logging of actions, errors, and debug information for tracking execution and aiding in troubleshooting.

## Directory Structure

*   `main.py`: The main entry point to run workflows. It parses command-line arguments and initializes the workflow engine.
*   `workflow_engine.py`: Contains the core logic for interpreting and executing workflow files. It manages steps, actions, and transitions.
*   `screen_interaction.py`: Provides functions for screen capture and finding images on the screen.
*   `input_simulation.py`: Handles the simulation of mouse movements, clicks, and keyboard inputs.
*   `config_loader.py`: Responsible for loading and validating workflow configuration files (JSON).
*   `workflows/`: This directory should contain your JSON workflow definition files (e.g., `sample_workflow.json`).
*   `images/`: This directory is intended to store template images that your workflows will use for image recognition tasks.

## Setup and Installation

1.  **Prerequisites**:
    *   Python 3 (tested with Python 3.7+)
    *   Access to a graphical desktop environment (for PyAutoGUI to control mouse/keyboard and find images).

2.  **Dependencies**:
    *   `PyAutoGUI`: For screen interaction and input simulation.
    *   `Pillow`: An image processing library, used by PyAutoGUI (often installed as a dependency of PyAutoGUI).

3.  **Installation**:
    You can install the necessary Python packages using pip:
    ```bash
    pip install pyautogui pillow
    ```
    On some Linux systems, you might need to install additional dependencies for PyAutoGUI to handle screenshots, such as `scrot`:
    ```bash
    sudo apt-get install scrot
    ```
    Please refer to the PyAutoGUI documentation for any platform-specific setup.

## Workflow Configuration (`workflows/*.json`)

Workflows are defined in JSON files. Here's the basic structure:

*   **`name`** (string): A descriptive name for the workflow.
*   **`start_step_id`** (string | number): The `id` of the first step to be executed when the workflow starts.
*   **`variables`** (object, optional): A dictionary where you can define global variables. These variables can be accessed and modified by workflow steps using the `{{variables.your_variable_name}}` syntax in parameters.
*   **`steps`** (array): A list of step objects, each defining an action to be performed.

### Step Object Structure

Each step object in the `steps` array has the following structure:

*   **`id`** (string | number): A unique identifier for this step within the workflow.
*   **`description`** (string): A human-readable description of what the step does. This is useful for understanding and debugging workflows.
*   **`action`** (string): The type of action this step will perform (e.g., "find_image_and_click", "type_text").
*   **`parameters`** (object): A dictionary of parameters specific to the chosen `action`.
*   **`on_success`** (string | number, optional): The `id` of the step to execute next if the current step completes successfully. If "exit", the workflow terminates. If omitted, the engine attempts to proceed to the next step in the JSON list; if it's the last step, the workflow exits.
*   **`on_failure`** (string | number, optional): The `id` of the step to execute next if the current step fails (e.g., an image is not found, or a required parameter is missing). If "exit", the workflow terminates. If omitted, a failure in a step will cause the workflow to terminate.

### Available Actions and Parameters

Here are the actions supported by the `workflow_engine`:

1.  **`debug_print`**: Prints a message to the console (and log).
    *   `parameters`:
        *   `message` (string): The message to print. Supports variable substitution.
        ```json
        {
            "id": "log_message",
            "action": "debug_print",
            "parameters": {"message": "Current user is {{variables.username}}"}
        }
        ```

2.  **`wait`**: Pauses the workflow execution for a specified duration.
    *   `parameters`:
        *   `seconds` (number): The number of seconds to wait.
        ```json
        {
            "id": "short_pause",
            "action": "wait",
            "parameters": {"seconds": 2.5}
        }
        ```

3.  **`find_image_and_click`**: Searches for a template image on the screen and clicks it if found.
    *   `parameters`:
        *   `image_path` (string): Path to the template image file (e.g., "images/button.png").
        *   `timeout` (number, optional, default: 10): Maximum time in seconds to wait for the image to appear.
        *   `confidence_threshold` (number, optional, default: 0.9): The confidence level for image matching (0.0 to 1.0). Higher is stricter.
        *   `button` (string, optional, default: "left"): The mouse button to click ('left', 'middle', 'right').
        *   `offset_x` (number, optional, default: 0): Horizontal offset in pixels from the center of the found image to click.
        *   `offset_y` (number, optional, default: 0): Vertical offset in pixels from the center of the found image to click.
        ```json
        {
            "id": "click_play_button",
            "action": "find_image_and_click",
            "parameters": {
                "image_path": "images/play_button.png", 
                "timeout": 5,
                "confidence_threshold": 0.85
            }
        }
        ```

4.  **`type_text`**: Simulates typing a string of text.
    *   `parameters`:
        *   `text` (string): The text to type. Supports variable substitution.
        ```json
        {
            "id": "enter_username",
            "action": "type_text",
            "parameters": {"text": "{{variables.username}}"}
        }
        ```

5.  **`press_key`**: Simulates pressing a single keyboard key.
    *   `parameters`:
        *   `key` (string): The name of the key to press (e.g., 'enter', 'esc', 'f1', 'a', 'ctrl'). Refer to PyAutoGUI documentation for key names.
        ```json
        {
            "id": "submit_form",
            "action": "press_key",
            "parameters": {"key": "enter"}
        }
        ```

6.  **`mouse_click_coordinates`**: Clicks the mouse at specified screen coordinates.
    *   `parameters`:
        *   `x` (number): The x-coordinate on the screen.
        *   `y` (number): The y-coordinate on the screen.
        *   `button` (string, optional, default: "left"): The mouse button to click.
        ```json
        {
            "id": "click_specific_point",
            "action": "mouse_click_coordinates",
            "parameters": {"x": 150, "y": 300, "button": "right"}
        }
        ```

7.  **`set_variable`**: Sets or updates a variable in the workflow's global `variables` dictionary.
    *   `parameters`:
        *   `variable_name` (string): The name of the variable to create or update (e.g., "user_id", "status_message"). This name must be a literal string and cannot itself be a variable placeholder.
        *   `value` (any): The value to assign to the variable. This value can be a literal (string, number, boolean) or use variable substitution to derive its value from other variables (e.g., `"{{variables.base_path}}/data.txt"`).
        ```json
        {
            "id": "store_item_id",
            "action": "set_variable",
            "parameters": {"variable_name": "selected_item", "value": "item123"}
        },
        {
            "id": "update_counter",
            "action": "set_variable",
            "parameters": {"variable_name": "retry_count", "value": "{{variables.retry_count}} + 1"} 
        }
        ```
        *(Note: The example `{{variables.retry_count}} + 1` for `set_variable` implies that the value resolution mechanism would need to support expression evaluation, which is an advanced feature not explicitly implemented by default. Simple string substitution is standard.)*

### Variable Substitution

Parameters for actions can include dynamic values by using variable substitution. The syntax is `{{variables.your_variable_name}}`. When a step is executed, these placeholders are replaced with the current value of the specified variable from the workflow's `variables` dictionary.

Example:
If `variables` contains `{"username": "test_user"}`, then a parameter `{"message": "Hello, {{variables.username}}!"}` would resolve to `{"message": "Hello, test_user!"}`.

## Running the Script

To execute a workflow, run `main.py` from your terminal:

```bash
python main.py --workflow path/to/your_workflow.json
```

For example, to run the sample workflow:

```bash
python main.py --workflow workflows/sample_workflow.json
```

You can control the verbosity of the logging output using the `--loglevel` argument:

```bash
python main.py --workflow workflows/sample_workflow.json --loglevel DEBUG
```

Available log levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Creating Template Images

Effective image recognition relies on good template images. Here are some tips:

*   **Clarity and Uniqueness**: The template image should be clear, distinct, and uniquely identify the UI element you want to interact with.
*   **Small but Sufficient**: Crop the image to be as small as possible while still containing enough unique features for reliable detection. Avoid including too much background that might change.
*   **Consistent State**: Capture the template image when the UI element is in the state you expect it to be in when the automation runs.
*   **Tools**: Use any screenshot tool (e.g., Snipping Tool on Windows, `flameshot` or `gnome-screenshot` on Linux, native macOS screenshot tools) to capture these images. Save them in a common format like PNG.
*   **Storage**: Store your template images in the `images/` directory or a sub-directory, and use relative paths in your workflow JSON (e.g., `images/my_button.png`).

## Example

Refer to the `workflows/sample_workflow.json` file for a basic example of a workflow structure. This sample demonstrates a few actions like printing messages, waiting, and attempting to find an image (which is expected to fail gracefully in the sample as no `dummy_target.png` is provided).

## Contributing

(Placeholder for future contribution guidelines, if any.)

## License

(Placeholder for license information - e.g., MIT, Apache 2.0. If no license is chosen, it's typically proprietary.)
