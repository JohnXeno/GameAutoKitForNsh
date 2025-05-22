import pyautogui
import time
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def take_screenshot(region=None):
    """
    Captures a screenshot of the specified region or the entire screen.

    Args:
        region (tuple, optional): A tuple (left, top, width, height) 
                                  specifying the region to capture. 
                                  Defaults to None (entire screen).

    Returns:
        PIL.Image.Image: The captured screenshot as a Pillow Image object.
    """
    screenshot = pyautogui.screenshot(region=region)
    return screenshot

def find_image_on_screen(template_image_path, confidence_threshold=0.8):
    """
    Finds an image on the screen based on a template image.

    Args:
        template_image_path (str): The path to the template image file.
        confidence_threshold (float, optional): The confidence level for image matching. 
                                               Defaults to 0.8.

    Returns:
        tuple: (x, y) coordinates of the center of the found image, or None if not found.
    """
    try:
        logger.debug("Attempting to locate '%s' on screen with confidence %s.", template_image_path, confidence_threshold)
        location = pyautogui.locateCenterOnScreen(template_image_path, confidence=confidence_threshold)
        if location:
            logger.debug("Image '%s' found at %s.", template_image_path, location)
        else:
            logger.debug("Image '%s' not found on screen (locateCenterOnScreen returned None).", template_image_path)
        return location
    except FileNotFoundError:
        logger.error("Template image file not found at path: '%s'.", template_image_path)
        return None
    except pyautogui.ImageNotFoundException: 
        # This exception is not actually raised by locateCenterOnScreen, 
        # it returns None instead. But good to keep for other pyautogui functions.
        logger.error("ImageNotFoundException for template '%s'. This typically means PyAutoGUI did not find the image.", template_image_path)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred in find_image_on_screen for template '%s': %s", template_image_path, e, exc_info=True)
        return None


def wait_for_image(template_image_path, timeout=30, confidence_threshold=0.8, poll_interval=0.5):
    """
    Waits for a specific image to appear on the screen.

    Args:
        template_image_path (str): Path to the template image file.
        timeout (int, optional): Maximum time (in seconds) to wait for the image. 
                                 Defaults to 30.
        confidence_threshold (float, optional): Confidence level for image matching. 
                                               Defaults to 0.8.
        poll_interval (float, optional): Time interval (in seconds) between search attempts. 
                                         Defaults to 0.5.

    Returns:
        tuple: (x, y) coordinates of the center of the found image, or None if timeout.
    """
    start_time = time.time()
    logger.info("Waiting for image '%s' to appear (timeout=%ss, confidence=%s).", template_image_path, timeout, confidence_threshold)
    while time.time() - start_time < timeout:
        location = find_image_on_screen(template_image_path, confidence_threshold=confidence_threshold) # Pass confidence here
        if location:
            logger.info("Image '%s' found at %s after %s seconds.", template_image_path, location, round(time.time() - start_time, 2))
            return location
        logger.debug("Image '%s' not yet found. Sleeping for %ss.", template_image_path, poll_interval)
        time.sleep(poll_interval)
    logger.warning("Timeout: Image '%s' not found within %s seconds.", template_image_path, timeout)
    return None

if __name__ == '__main__':
    # Basic logging setup for standalone testing of this module
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("--- Testing screen_interaction module ---")
    # Example usage (optional, for testing)
    
    # Test take_screenshot
    # logger.info("Testing take_screenshot()... (will capture entire screen)")
    # try:
    #     full_screen_img = take_screenshot()
    #     if full_screen_img:
    #         logger.info("Full screen screenshot captured. Size: %s", full_screen_img.size)
    #         # full_screen_img.save("fullscreen_test.png") # Optional: save to check
    #     else:
    #         logger.error("take_screenshot() returned None.")
    # except Exception as e:
    #     logger.error("Error during take_screenshot test: %s", e)

    # Test find_image_on_screen (requires a 'template.png' to exist for a meaningful test)
    # Create a dummy template file for testing
    try:
        from PIL import Image as PImage
        dummy_image = PImage.new('RGB', (60, 30), color = 'red')
        dummy_image.save("dummy_template_screen.png")
        logger.info("Created dummy_template_screen.png for testing find_image_on_screen and wait_for_image.")

        # Note: For find_image_on_screen to actually find something, 
        # "dummy_template_screen.png" would need to be visible on the screen when this runs.
        # This test will likely result in "not found" unless you manually make it visible.
        logger.info("Testing find_image_on_screen('dummy_template_screen.png')...")
        location = find_image_on_screen("dummy_template_screen.png", confidence_threshold=0.7)
        if location:
            logger.info("find_image_on_screen found dummy_template_screen.png at: %s", location)
        else:
            logger.info("find_image_on_screen did not find dummy_template_screen.png (this is expected if not visible).")

        logger.info("Testing wait_for_image('dummy_template_screen.png', timeout=2)...")
        location_wait = wait_for_image("dummy_template_screen.png", timeout=2, confidence_threshold=0.7)
        if location_wait:
            logger.info("wait_for_image found dummy_template_screen.png at: %s", location_wait)
        else:
            logger.info("wait_for_image timed out for dummy_template_screen.png (expected if not visible).")

        logger.info("Testing find_image_on_screen with a non-existent template...")
        location_non_existent = find_image_on_screen("non_existent_template.png")
        if location_non_existent is None:
            logger.info("find_image_on_screen correctly handled non-existent template (returned None).")

    except ImportError:
        logger.warning("Pillow (PIL) is not installed. Skipping some __main__ tests for screen_interaction.")
    except Exception as e:
        logger.error("Error in __main__ test setup for screen_interaction: %s", e)
    finally:
        import os
        if os.path.exists("dummy_template_screen.png"):
            os.remove("dummy_template_screen.png")
        # if os.path.exists("fullscreen_test.png"):
        #     os.remove("fullscreen_test.png")


    # take_screenshot()  # Capture entire screen
    # region_to_capture = (100, 100, 500, 300) # Example region
    # captured_image = take_screenshot(region=region_to_capture)
    # if captured_image: captured_image.show() # Display the captured image
    
    # Example for find_image_on_screen (assuming you have 'template.png' in the same directory)
    # location = find_image_on_screen('template.png')
    # if location:
    #     logger.info(f"Image found at: {location}")
    # else:
    #     logger.info("Image not found.")
    logger.info("screen_interaction.py logging integration complete.")
