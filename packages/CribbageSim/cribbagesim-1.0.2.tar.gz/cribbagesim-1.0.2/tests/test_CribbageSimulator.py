# Standard
import logging
import unittest
import io
from unittest.mock import patch

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.deck import StackedDeck
from CribbageSim.CribbageSimulator import CribbageSimulator
from CribbageSim.CribbageGame import CribbageGame
from CribbageSim.CribbagePlayStrategy import InteractiveCribbagePlayStrategy

class Test_CribbageSimulator(unittest.TestCase):
 
    # Patch results in dealer scoring a pair with their first card played, and winning the game.
    @patch('sys.stdin', io.StringIO('4\n3\n2\n1\n0\n2\n'))
    def test_logging_info(self):
        
        # Set up logging
        sim = CribbageSimulator()
        sim.setup_logging()

        # Create an interactive cribbage game
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = InteractiveCribbagePlayStrategy())

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        # Dealer will be dealt cards 7 - 12
        # Starter will be card 13
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','3'), Card('H','8'), Card('H','K'),
                     Card('S','Q'), Card('H','7'), Card('C','6'), Card('D','A'), Card('H','10'), Card('S','K'),
                     Card('H','5')]
        sd.add_cards(card_list)
        
        game._deal._deck = sd
        
        # Player1 will be one point from winning when the game begins, so the first score for that player will win the game.
        game._board.peg_for_player1(120)
        
        # Test that logger works as expected
        with self.assertLogs('cribbage_logger', level=logging.INFO) as cm:
            game.play()
        
        # Test that the info messages sent to the logger are as expected
        self.assertEqual(cm.output[0], 'INFO:cribbage_logger:Starting a new game of cribbage with human_player vs machine_player.')    
        self.assertEqual(cm.output[1], 'INFO:cribbage_logger:Player human_player will deal.')
        self.assertEqual(cm.output[2], 'INFO:cribbage_logger:Hand for CribbagePlayers.PLAYER_1 after dealing: QS 7H 6C AD 10H KS')
        
    # Patch results in dealer scoring a pair with their first card played, and winning the game.
    @patch('sys.stdin', io.StringIO('4\n3\n2\n1\n0\n2\n'))
    def test_logging_debug(self):

        # Set up logging
        sim = CribbageSimulator()
        sim.setup_logging()

        # Create an interactive cribbage game
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = InteractiveCribbagePlayStrategy())

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        # Dealer will be dealt cards 7 - 12
        # Starter will be card 13
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','3'), Card('H','8'), Card('H','K'),
                     Card('S','Q'), Card('H','7'), Card('C','6'), Card('D','A'), Card('H','10'), Card('S','K'),
                     Card('H','5')]
        sd.add_cards(card_list)
        
        game._deal._deck = sd
        
        # Player1 will be one point from winning when the game begins, so the first score for that player will win the game.
        game._board.peg_for_player1(120)
        
        # Test that logger works as expected
        with self.assertLogs('cribbage_logger', level=logging.DEBUG) as cm:
            game.play()
        
        # Test that the debug messages sent to the logger are as expected
        self.assertEqual(cm.output[0], 'INFO:cribbage_logger:Starting a new game of cribbage with human_player vs machine_player.')    
        self.assertEqual(cm.output[1], 'INFO:cribbage_logger:Player human_player will deal.')    
        self.assertEqual(cm.output[2], 'DEBUG:cribbage_logger:Hand for CribbagePlayers.PLAYER_2 after deal: 10S 5C 10D 3C 8H KH')


if __name__ == '__main__':
    unittest.main()
