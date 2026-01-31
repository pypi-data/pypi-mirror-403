# Standard
import unittest

# Local
from CribbageSim.CribbageBoard import CribbageBoard

class Test_CribbageBoard(unittest.TestCase):
    
    def test_peg_for_player1(self):
        
        board = CribbageBoard()
        return_val = board.peg_for_player1(6)
        
        # Did we get the expected return value?
        exp_val = 6
        self.assertEqual(exp_val, return_val)

        board.peg_for_player1(5)

        # Are the leading and trailing pegs where they are expected?
        exp_val = (11, 6)
        act_val = (board._player1_current, board._player1_previous)
        self.assertTupleEqual(exp_val, act_val)

    def test_peg_for_player2(self):
        
        board = CribbageBoard()
        return_val = board.peg_for_player2(3)
        
        # Did we get the expected return value?
        exp_val = 3
        self.assertEqual(exp_val, return_val)

        board.peg_for_player2(5)

        # Are the leading and trailing pegs where they are expected?
        exp_val = (8, 3)
        act_val = (board._player2_current, board._player2_previous)
        self.assertTupleEqual(exp_val, act_val)

    def test_get_player1_status(self):
        
        board = CribbageBoard()
        board.peg_for_player1(6)
        board.peg_for_player1(5)
        
        # Are the leading and trailing pegs reported where they are expected?
        exp_val = (11, 6)
        act_val = board.get_player1_status()
        self.assertTupleEqual(exp_val, act_val)

    def test_get_player2_status(self):
        
        board = CribbageBoard()
        board.peg_for_player2(3)
        board.peg_for_player2(5)
        
        # Are the leading and trailing pegs reported where they are expected?
        exp_val = (8, 3)
        act_val = board.get_player2_status()
        self.assertTupleEqual(exp_val, act_val)

    def test_get_scores(self):

        board = CribbageBoard()
        board.peg_for_player1(6)
        board.peg_for_player1(5)
        board.peg_for_player2(3)
        board.peg_for_player2(5)

        # Are the scores reported as expected?
        exp_val = (11, 8)
        act_val = board.get_scores()
        self.assertTupleEqual(exp_val, act_val)

    def test_dunder_str(self):

        board = CribbageBoard()
        board.peg_for_player1(6)
        board.peg_for_player1(5)
        board.peg_for_player2(3)
        board.peg_for_player2(5)

        # Is the board converted to a string as expected?
        exp_val = f"Player 1: Current = 11, Previous = 6\nPlayer 2: Current = 8, Previous = 3"
        act_val = str(board)
        self.assertEqual(exp_val, act_val)

    
if __name__ == '__main__':
    unittest.main()

