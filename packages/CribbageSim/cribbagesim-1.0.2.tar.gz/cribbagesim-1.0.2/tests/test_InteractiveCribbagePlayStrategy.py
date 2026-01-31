# Standard
import unittest
import io
from unittest.mock import patch

# Local
from CribbageSim.CribbagePlayStrategy import InteractiveCribbagePlayStrategy


class Test_test_InteractiveCribbagePlayStrategy(unittest.TestCase):
    
    # Patch results in choosing to continue game.
    @patch('sys.stdin', io.StringIO('c\n'))
    def test_continue_save_end_continue(self):
        
        icps = InteractiveCribbagePlayStrategy()
        act_val = icps.continue_save_end()
        exp_val = (True, False)
        self.assertEqual(exp_val, act_val)
        
    # Patch results in choosing to end game and save state.
    @patch('sys.stdin', io.StringIO('s\n'))
    def test_continue_save_end_save(self):
        
        icps = InteractiveCribbagePlayStrategy()
        act_val = icps.continue_save_end()
        exp_val = (False, True)
        self.assertEqual(exp_val, act_val)
        
    # Patch results in choosing to end game and NOT save state.
    @patch('sys.stdin', io.StringIO('e\n'))
    def test_continue_save_end_end(self):
        
        icps = InteractiveCribbagePlayStrategy()
        act_val = icps.continue_save_end()
        exp_val = (False, False)
        self.assertEqual(exp_val, act_val)
 

if __name__ == '__main__':
    unittest.main()
