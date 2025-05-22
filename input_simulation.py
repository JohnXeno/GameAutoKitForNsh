import pyautogui
import time
import logging

logger = logging.getLogger(__name__)

def mouse_move(x, y, duration=0.2):
    """
    Moves the mouse cursor to the specified (x, y) coordinates.

    Args:
        x (int): The x-coordinate to move the mouse to.
        y (int): The y-coordinate to move the mouse to.
        duration (float, optional): The time in seconds to take to move the mouse. 
                                    Defaults to 0.2.
    """
    logger.debug("Moving mouse to (x=%s, y=%s) over %ss", x, y, duration)
    pyautogui.moveTo(x, y, duration=duration)

def mouse_click(x=None, y=None, button='left', clicks=1, interval=0.1, duration=0.0):
    """
    Simulates a mouse click at the specified coordinates or current position.

    Args:
        x (int, optional): The x-coordinate to move to before clicking. Defaults to None.
        y (int, optional): The y-coordinate to move to before clicking. Defaults to None.
        button (str, optional): The mouse button to click ('left', 'middle', 'right'). 
                                Defaults to 'left'.
        clicks (int, optional): The number of times to click. Defaults to 1.
        interval (float, optional): The time in seconds between clicks. Defaults to 0.1.
        duration (float, optional): The time in seconds to move the mouse. Defaults to 0.0.
    """
    if x is not None and y is not None:
        logger.debug("Moving mouse to (x=%s, y=%s) before clicking.", x, y)
        pyautogui.moveTo(x, y, duration=duration)
    logger.debug("Clicking mouse: button=%s, clicks=%s, interval=%s", button, clicks, interval)
    pyautogui.click(button=button, clicks=clicks, interval=interval)

def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5, button='left'):
    """
    Drags the mouse from (start_x, start_y) to (end_x, end_y).

    Args:
        start_x (int): The starting x-coordinate of the drag.
        start_y (int): The starting y-coordinate of the drag.
        end_x (int): The ending x-coordinate of the drag.
        end_y (int): The ending y-coordinate of the drag.
        duration (float, optional): The time in seconds for the drag operation. 
                                    Defaults to 0.5.
        button (str, optional): The mouse button to hold during the drag 
                                ('left', 'middle', 'right'). Defaults to 'left'.
    """
    logger.debug("Dragging mouse from (x=%s, y=%s) to (x=%s, y=%s) over %ss, button=%s", start_x, start_y, end_x, end_y, duration, button)
    pyautogui.moveTo(start_x, start_y, duration=0.0) # Move to start position instantly
    pyautogui.dragTo(end_x, end_y, duration=duration, button=button)

def key_press(key_name):
    """
    Simulates a full key press (down and up) for the given key_name.

    Args:
        key_name (str): The name of the key to press (e.g., 'enter', 'a', 'ctrl').
    """
    logger.debug("Pressing key: '%s'", key_name)
    pyautogui.press(key_name)

def key_down(key_name):
    """
    Simulates pressing and holding down the specified key_name.

    Args:
        key_name (str): The name of the key to hold down (e.g., 'ctrl', 'shift').
    """
    logger.debug("Holding down key: '%s'", key_name)
    pyautogui.keyDown(key_name)

def key_up(key_name):
    """
    Simulates releasing the specified key_name.

    Args:
        key_name (str): The name of the key to release (e.g., 'ctrl', 'shift').
    """
    logger.debug("Releasing key: '%s'", key_name)
    pyautogui.keyUp(key_name)

def type_string(text, interval=0.05):
    """
    Types the characters in the text string one by one.

    Args:
        text (str): The string of characters to type.
        interval (float, optional): The time in seconds between each key press. 
                                    Defaults to 0.05.
    """
    # Masking text in log if it's sensitive could be an option here if needed,
    # but for now, we'll log the action of typing.
    logger.debug("Typing string (first 20 chars): '%.20s...' with interval %ss", text, interval)
    pyautogui.write(text, interval=interval)

if __name__ == '__main__':
    # Basic logging setup for standalone testing of this module
    if not logging.getLogger().hasHandlers(): # Avoid reconfiguring if already done by main.py
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Testing input_simulation module ---")
    # Example usage (optional, for testing)
    
    logger.info("Testing mouse_move(100, 100)...")
    mouse_move(100, 100)
    time.sleep(0.5)
    
    logger.info("Testing mouse_click(200, 200, button='left')...")
    mouse_click(200, 200, button='left')
    time.sleep(0.5)

    # logger.info("Testing mouse_drag(300, 300, 400, 400)...")
    # mouse_drag(300, 300, 400, 400) # Be careful with drag tests
    # time.sleep(0.5)

    # To test key presses, you'd typically need an active input field.
    # For example, open a text editor manually before running this part.
    # logger.info("Testing key_press('a')... (requires an active input field)")
    # key_press('a')
    # time.sleep(0.5)

    # logger.info("Testing type_string('hello world')... (requires an active input field)")
    # type_string("hello world example for testing")
    # time.sleep(0.5)

    # logger.info("Testing key_down('shift') then key_press('a') then key_up('shift')...")
    # key_down('shift')
    # key_press('a') # Should type 'A'
    # key_up('shift')
    # time.sleep(0.5)

    logger.info("input_simulation.py logging integration complete and __main__ tests updated.")
