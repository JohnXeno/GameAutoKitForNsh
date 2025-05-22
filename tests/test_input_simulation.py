import unittest
import os
import sys
from unittest.mock import patch

# Adjust path to import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import input_simulation

# Test class for input_simulation module
class TestInputSimulation(unittest.TestCase):

    @patch('input_simulation.pyautogui')
    def test_mouse_move(self, mock_pyautogui):
        """Test mouse_move function."""
        input_simulation.mouse_move(100, 200, duration=0.5)
        mock_pyautogui.moveTo.assert_called_once_with(100, 200, duration=0.5)

    @patch('input_simulation.pyautogui')
    def test_mouse_move_default_duration(self, mock_pyautogui):
        """Test mouse_move function with default duration."""
        input_simulation.mouse_move(150, 250)
        mock_pyautogui.moveTo.assert_called_once_with(150, 250, duration=0.2) # Default duration

    @patch('input_simulation.pyautogui')
    def test_mouse_click_with_coordinates(self, mock_pyautogui):
        """Test mouse_click function when x, y coordinates are provided."""
        input_simulation.mouse_click(x=50, y=60, button='right', clicks=2, interval=0.3, duration=0.1)
        mock_pyautogui.moveTo.assert_called_once_with(50, 60, duration=0.1)
        mock_pyautogui.click.assert_called_once_with(button='right', clicks=2, interval=0.3)

    @patch('input_simulation.pyautogui')
    def test_mouse_click_without_coordinates(self, mock_pyautogui):
        """Test mouse_click function when x, y coordinates are not provided."""
        input_simulation.mouse_click(button='left', clicks=1, interval=0.1)
        mock_pyautogui.moveTo.assert_not_called() # moveTo should not be called
        mock_pyautogui.click.assert_called_once_with(button='left', clicks=1, interval=0.1)

    @patch('input_simulation.pyautogui')
    def test_mouse_click_defaults(self, mock_pyautogui):
        """Test mouse_click with default parameters and no coordinates."""
        input_simulation.mouse_click()
        mock_pyautogui.moveTo.assert_not_called()
        mock_pyautogui.click.assert_called_once_with(button='left', clicks=1, interval=0.1) # Default values

    @patch('input_simulation.pyautogui')
    def test_mouse_click_defaults_with_coordinates(self, mock_pyautogui):
        """Test mouse_click with default parameters and provided coordinates."""
        input_simulation.mouse_click(x=10, y=20)
        mock_pyautogui.moveTo.assert_called_once_with(10, 20, duration=0.0) # Default duration for move before click
        mock_pyautogui.click.assert_called_once_with(button='left', clicks=1, interval=0.1)

    @patch('input_simulation.pyautogui')
    def test_mouse_drag(self, mock_pyautogui):
        """Test mouse_drag function."""
        input_simulation.mouse_drag(start_x=10, start_y=20, end_x=100, end_y=200, duration=0.7, button='middle')
        # Check that moveTo is called first to go to the start position
        mock_pyautogui.moveTo.assert_called_once_with(10, 20, duration=0.0) # Instant move to start
        # Check that dragTo is called with the correct parameters
        mock_pyautogui.dragTo.assert_called_once_with(100, 200, duration=0.7, button='middle')

    @patch('input_simulation.pyautogui')
    def test_mouse_drag_defaults(self, mock_pyautogui):
        """Test mouse_drag function with default parameters."""
        input_simulation.mouse_drag(5, 15, 50, 150)
        mock_pyautogui.moveTo.assert_called_once_with(5, 15, duration=0.0)
        mock_pyautogui.dragTo.assert_called_once_with(50, 150, duration=0.5, button='left') # Defaults

    @patch('input_simulation.pyautogui')
    def test_key_press(self, mock_pyautogui):
        """Test key_press function."""
        input_simulation.key_press('enter')
        mock_pyautogui.press.assert_called_once_with('enter')

    @patch('input_simulation.pyautogui')
    def test_key_down(self, mock_pyautogui):
        """Test key_down function."""
        input_simulation.key_down('ctrl')
        mock_pyautogui.keyDown.assert_called_once_with('ctrl')

    @patch('input_simulation.pyautogui')
    def test_key_up(self, mock_pyautogui):
        """Test key_up function."""
        input_simulation.key_up('shift')
        mock_pyautogui.keyUp.assert_called_once_with('shift')

    @patch('input_simulation.pyautogui')
    def test_type_string(self, mock_pyautogui):
        """Test type_string function."""
        input_simulation.type_string("hello world!", interval=0.07)
        mock_pyautogui.write.assert_called_once_with("hello world!", interval=0.07)

    @patch('input_simulation.pyautogui')
    def test_type_string_default_interval(self, mock_pyautogui):
        """Test type_string function with default interval."""
        input_simulation.type_string("testing")
        mock_pyautogui.write.assert_called_once_with("testing", interval=0.05) # Default interval

if __name__ == '__main__':
    unittest.main()
