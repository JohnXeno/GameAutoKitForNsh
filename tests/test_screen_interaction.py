import unittest
import os
import sys
import time # For testing timeout duration
from unittest.mock import patch, MagicMock

# Adjust path to import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import screen_interaction
from PIL import Image # For type hinting and spec for MagicMock

class TestScreenInteraction(unittest.TestCase):

    @patch('screen_interaction.pyautogui')
    def test_take_screenshot_no_region(self, mock_pyautogui):
        """Test taking a screenshot of the entire screen."""
        mock_screenshot_image = MagicMock(spec=Image.Image)
        mock_pyautogui.screenshot.return_value = mock_screenshot_image

        returned_image = screen_interaction.take_screenshot()

        mock_pyautogui.screenshot.assert_called_once_with(region=None)
        self.assertIs(returned_image, mock_screenshot_image)

    @patch('screen_interaction.pyautogui')
    def test_take_screenshot_with_region(self, mock_pyautogui):
        """Test taking a screenshot of a specified region."""
        test_region = (0, 0, 100, 100)
        mock_screenshot_image = MagicMock(spec=Image.Image)
        mock_pyautogui.screenshot.return_value = mock_screenshot_image

        returned_image = screen_interaction.take_screenshot(region=test_region)

        mock_pyautogui.screenshot.assert_called_once_with(region=test_region)
        self.assertIs(returned_image, mock_screenshot_image)

    @patch('screen_interaction.pyautogui')
    def test_find_image_on_screen_found(self, mock_pyautogui):
        """Test finding an image when it's present on screen."""
        mock_pyautogui.locateCenterOnScreen.return_value = (100, 150) # Simulate found coordinates
        
        coords = screen_interaction.find_image_on_screen("dummy_path.png", confidence_threshold=0.7)
        
        mock_pyautogui.locateCenterOnScreen.assert_called_once_with("dummy_path.png", confidence=0.7)
        self.assertEqual(coords, (100, 150))

    @patch('screen_interaction.pyautogui')
    def test_find_image_on_screen_not_found(self, mock_pyautogui):
        """Test finding an image when it's not present on screen."""
        mock_pyautogui.locateCenterOnScreen.return_value = None # Simulate not found
        
        coords = screen_interaction.find_image_on_screen("dummy_path.png") # Uses default confidence
        
        mock_pyautogui.locateCenterOnScreen.assert_called_once_with("dummy_path.png", confidence=0.8) # Default confidence
        self.assertIsNone(coords)

    @patch('screen_interaction.pyautogui')
    @patch('screen_interaction.logger') # To check if error is logged
    def test_find_image_on_screen_file_not_found_error(self, mock_logger, mock_pyautogui):
        """Test behavior when the template image file does not exist."""
        mock_pyautogui.locateCenterOnScreen.side_effect = FileNotFoundError("Mocked: File not found")
        
        coords = screen_interaction.find_image_on_screen("non_existent.png")
        
        self.assertIsNone(coords)
        mock_logger.error.assert_called_with("Template image file not found at path: '%s'.", "non_existent.png")

    @patch('screen_interaction.time.sleep') 
    @patch('screen_interaction.find_image_on_screen') # Mocking its own module's function
    def test_wait_for_image_found_immediately(self, mock_find_image, mock_sleep):
        """Test wait_for_image when the image is found on the first attempt."""
        mock_find_image.return_value = (200, 250)
        
        coords = screen_interaction.wait_for_image("dummy.png", timeout=5, poll_interval=0.1, confidence_threshold=0.85)
        
        self.assertEqual(coords, (200, 250))
        # wait_for_image calls find_image_on_screen with confidence_threshold
        mock_find_image.assert_called_once_with("dummy.png", confidence_threshold=0.85)
        mock_sleep.assert_not_called()

    @patch('screen_interaction.time.sleep')
    @patch('screen_interaction.find_image_on_screen')
    def test_wait_for_image_found_after_retries(self, mock_find_image, mock_sleep):
        """Test wait_for_image when the image is found after a few retries."""
        mock_find_image.side_effect = [None, None, (300, 350)] # Found on 3rd attempt
        
        coords = screen_interaction.wait_for_image("dummy.png", timeout=5, poll_interval=0.1, confidence_threshold=0.7)
        
        self.assertEqual(coords, (300, 350))
        self.assertEqual(mock_find_image.call_count, 3)
        # Check that all calls to find_image_on_screen used the correct confidence_threshold
        mock_find_image.assert_any_call("dummy.png", confidence_threshold=0.7)
        self.assertEqual(mock_sleep.call_count, 2) # Sleep called twice before success

    @patch('screen_interaction.time.sleep')
    @patch('screen_interaction.find_image_on_screen')
    @patch('screen_interaction.logger')
    def test_wait_for_image_timeout(self, mock_logger, mock_find_image, mock_sleep):
        """Test wait_for_image when the image is never found and times out."""
        mock_find_image.return_value = None # Image never found
        
        test_timeout = 0.5  # Using a float value for timeout
        test_poll_interval = 0.1
        
        start_time = time.monotonic() # Use monotonic clock for duration measurement
        coords = screen_interaction.wait_for_image("dummy.png", timeout=test_timeout, poll_interval=test_poll_interval)
        end_time = time.monotonic()
        
        duration = end_time - start_time
        
        self.assertIsNone(coords)
        # Number of calls: timeout / poll_interval. E.g., 0.5 / 0.1 = 5 calls
        # It might be slightly more due to the loop condition check time.
        # So, we check if it's approximately in the expected range.
        expected_calls_min = int(test_timeout / test_poll_interval)
        self.assertGreaterEqual(mock_find_image.call_count, expected_calls_min) 
        
        # Check if the function respected the timeout duration (approximately)
        # Allow for a small margin of error in timing
        self.assertTrue(test_timeout - test_poll_interval <= duration < test_timeout + (2*test_poll_interval), 
                        f"Duration {duration}s not within expected range of timeout {test_timeout}s")

        mock_logger.warning.assert_called_with("Timeout: Image '%s' not found within %s seconds.", "dummy.png", test_timeout)

if __name__ == '__main__':
    unittest.main()
