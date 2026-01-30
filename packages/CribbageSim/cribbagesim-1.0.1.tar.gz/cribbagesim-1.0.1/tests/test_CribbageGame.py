# Standard
import unittest
import io
from unittest.mock import patch

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.deck import StackedDeck
from CribbageSim.CribbagePlayStrategy import InteractiveCribbagePlayStrategy, HoyleishPlayerCribbagePlayStrategy, HoyleishDealerCribbagePlayStrategy
from CribbageSim.CribbageGame import CribbageGame, CribbageGameInfo

class Test_CribbageGame(unittest.TestCase):
    
    # Patch results in dealer scoring a pair with their first card played, and winning the game.
    @patch('sys.stdin', io.StringIO('4\n3\n2\n1\n0\n2\n'))
    def test_play_both_interactive_end_at_first_score(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        # Dealer will be dealt cards 7 - 12
        # Starter will be card 13
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','3'), Card('H','8'), Card('H','K'),
                     Card('S','Q'), Card('H','7'), Card('C','6'), Card('D','A'), Card('H','10'), Card('S','K'),
                     Card('H','5')]
        sd.add_cards(card_list)
        
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = InteractiveCribbagePlayStrategy())
        game._deal._deck = sd
        
        # Player1 will be one point from winning when the game begins, so the first score for that player will win the game.
        game._board.peg_for_player1(120)
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is Player1 score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been only 1 deal?
        exp_val = 1
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)

    @patch('sys.stdin', io.StringIO('3\n0\n3\n2\n1\n0\n2\n0\ng\n1\n0\n0\ng\n0\ng\nc\n1\n0\n2\n0\n1\n0\n1\n2\n0\n0\n0\n0\ng\n'))
    def test_play_both_interactive_end_at_second_show(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6 for deal 1, and cards 14 - 19 for deal 2
        # Dealer will be dealt cards 7 - 12 for deal 1, and cards 20 - 25 for deal 2
        # Starter will be card 13 for deal 1, and card 26 for deal 2
        card_list = [Card('H','4'), Card('H','9'), Card('C','10'), Card('S','A'), Card('C','J'), Card('C','5'),
                     Card('H','5'), Card('H','10'), Card('C','2'), Card('D','2'), Card('S','9'), Card('S','7'),
                     Card('S','4'),
                     Card('S','3'), Card('H','A'), Card('H','6'), Card('D','7'), Card('H','7'), Card('D','2'),
                     Card('D','3'), Card('C','J'), Card('H','9'), Card('D','J'), Card('S','J'), Card('D','A'),
                     Card('D','10')]
        sd.add_cards(card_list)
        
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = InteractiveCribbagePlayStrategy())
        game._deal._deck = sd
        
        # Player2 will win after dealing the second deal, and showing the crib 
        game._board.peg_for_player2(97)
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is Player2 score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # is Player1 score as expected?
        exp_val = 18
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 2 deals?
        exp_val = 2
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)

    @patch('sys.stdin', io.StringIO('3\n2\n0\n0\n1\ng\n0\nc\n1\n0\n2\n1\n1\n0\ng\n'))
    def test_play_one_interactive_end_at_second_show(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6 for deal 1, and cards 14 - 19 for deal 2
        # Dealer will be dealt cards 7 - 12 for deal 1, and cards 20 - 25 for deal 2
        # Starter will be card 13 for deal 1, and card 26 for deal 2
        card_list = [Card('H','4'), Card('H','9'), Card('C','10'), Card('S','A'), Card('C','J'), Card('C','5'),
                     Card('H','5'), Card('H','10'), Card('C','2'), Card('D','2'), Card('S','9'), Card('S','7'),
                     Card('S','4'),
                     Card('S','3'), Card('H','A'), Card('H','6'), Card('D','7'), Card('H','7'), Card('D','2'),
                     Card('D','3'), Card('C','J'), Card('H','9'), Card('D','J'), Card('S','J'), Card('D','A'),
                     Card('D','10')]
        sd.add_cards(card_list)
        
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        game._deal._deck = sd
        
        # Player2 will win after dealing the second deal, and showing the crib 
        game._board.peg_for_player2(100)
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is Player2 score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # is Player1 score as expected?
        exp_val = 17
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 2 deals?
        exp_val = 2
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)

    def test_play_both_automatic_end_player_show(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567890)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 98
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 8 deals?
        exp_val = 8
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(20, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(82, return_val.player1_total_show_score)
        self.assertEqual(26, return_val.player1_total_crib_score)
        self.assertEqual(27, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(58, return_val.player2_total_show_score)
        self.assertEqual(13, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)
        
    def test_play_both_automatic_end_dealer_show(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567891)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 99
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 8 deals?
        exp_val = 8
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(25, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(53, return_val.player1_total_show_score)
        self.assertEqual(21, return_val.player1_total_crib_score)
        self.assertEqual(18, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(91, return_val.player2_total_show_score)
        self.assertEqual(12, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_dealer_go_not_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567892)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 84
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(24, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(77, return_val.player1_total_show_score)
        self.assertEqual(20, return_val.player1_total_crib_score)
        self.assertEqual(29, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(43, return_val.player2_total_show_score)
        self.assertEqual(12, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)

    def test_play_both_automatic_end_dealer_follow(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567896)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 105
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(37, return_val.player1_total_play_score)
        self.assertEqual(2, return_val.player1_total_his_heals_score)
        self.assertEqual(72, return_val.player1_total_show_score)
        self.assertEqual(11, return_val.player1_total_crib_score)
        self.assertEqual(35, return_val.player2_total_play_score)
        self.assertEqual(2, return_val.player2_total_his_heals_score)
        self.assertEqual(44, return_val.player2_total_show_score)
        self.assertEqual(24, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)

    def test_play_both_automatic_end_dealer_crib(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567899)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 88
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 8 deals?
        exp_val = 8
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(19, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(51, return_val.player1_total_show_score)
        self.assertEqual(18, return_val.player1_total_crib_score)
        self.assertEqual(27, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(72, return_val.player2_total_show_score)
        self.assertEqual(25, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)
   
    def test_play_both_automatic_end_dealer_follow_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567903)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 92
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(39, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(65, return_val.player1_total_show_score)
        self.assertEqual(17, return_val.player1_total_crib_score)
        self.assertEqual(33, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(51, return_val.player2_total_show_score)
        self.assertEqual(8, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)

    def test_play_both_automatic_end_player_follow(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567909)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 99
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(22, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(61, return_val.player1_total_show_score)
        self.assertEqual(16, return_val.player1_total_crib_score)
        self.assertEqual(29, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(62, return_val.player2_total_show_score)
        self.assertEqual(30, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_player_follow_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567917)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 104
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 10 deals?
        exp_val = 10
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(24, return_val.player1_total_play_score)
        self.assertEqual(2, return_val.player1_total_his_heals_score)
        self.assertEqual(76, return_val.player1_total_show_score)
        self.assertEqual(20, return_val.player1_total_crib_score)
        self.assertEqual(17, return_val.player2_total_play_score)
        self.assertEqual(2, return_val.player2_total_his_heals_score)
        self.assertEqual(69, return_val.player2_total_show_score)
        self.assertEqual(16, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)

    def test_play_both_automatic_end_dealer_go_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567940)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 113
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(30, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(63, return_val.player1_total_show_score)
        self.assertEqual(28, return_val.player1_total_crib_score)
        self.assertEqual(31, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(66, return_val.player2_total_show_score)
        self.assertEqual(16, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player2_total_play_score + return_val.player2_total_his_heals_score + return_val.player2_total_show_score + return_val.player2_total_crib_score)

    def test_play_both_automatic_end_player_go_not_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234567983)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 87
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(25, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(54, return_val.player1_total_show_score)
        self.assertEqual(8, return_val.player1_total_crib_score)
        self.assertEqual(27, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(67, return_val.player2_total_show_score)
        self.assertEqual(27, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_dealer_his_heals(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234568026)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 104
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 10 deals?
        exp_val = 10
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(23, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(50, return_val.player1_total_show_score)
        self.assertEqual(31, return_val.player1_total_crib_score)
        self.assertEqual(34, return_val.player2_total_play_score)
        self.assertEqual(2, return_val.player2_total_his_heals_score)
        self.assertEqual(66, return_val.player2_total_show_score)
        self.assertEqual(19, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_dealer_go_play_score(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234568209)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 110
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 10 deals?
        exp_val = 10
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(26, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(56, return_val.player1_total_show_score)
        self.assertEqual(28, return_val.player1_total_crib_score)
        self.assertEqual(29, return_val.player2_total_play_score)
        self.assertEqual(2, return_val.player2_total_his_heals_score)
        self.assertEqual(68, return_val.player2_total_show_score)
        self.assertEqual(22, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_player_go_31(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234568435)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 118
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(33, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(65, return_val.player1_total_show_score)
        self.assertEqual(20, return_val.player1_total_crib_score)
        self.assertEqual(38, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(72, return_val.player2_total_show_score)
        self.assertEqual(12, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)

    def test_play_both_automatic_end_player_go_play_score(self):
        
        # Seed the random number generator
        from random import seed
        seed(1234568673)

        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        return_val = game.play()

        # Did Player2 win?
        exp_val = game._player2
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is winning player score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Is losing player score as expected?
        exp_val = 99
        act_val = return_val.losing_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been 9 deals?
        exp_val = 9
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)
        
        # Are the game scoring statistics as expected
        self.assertEqual(32, return_val.player1_total_play_score)
        self.assertEqual(0, return_val.player1_total_his_heals_score)
        self.assertEqual(50, return_val.player1_total_show_score)
        self.assertEqual(17, return_val.player1_total_crib_score)
        self.assertEqual(43, return_val.player2_total_play_score)
        self.assertEqual(0, return_val.player2_total_his_heals_score)
        self.assertEqual(54, return_val.player2_total_show_score)
        self.assertEqual(24, return_val.player2_total_crib_score)
        
        # Does losing player score check out?
        self.assertEqual(return_val.losing_player_final_score,
                         return_val.player1_total_play_score + return_val.player1_total_his_heals_score + return_val.player1_total_show_score + return_val.player1_total_crib_score)


    # Patch results in dealer scoring a pair after a go by their opponent and winning the game
    @patch('sys.stdin', io.StringIO('5\n4\n5\n4\n0\n0\n0\n2\ng\n0\n'))
    def test_play_both_interactive_end_at_go_combo(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        # Dealer will be dealt cards 7 - 12
        # Starter will be card 13
        card_list = [Card('S','10'), Card('C','K'), Card('D','10'), Card('C','9'), Card('H','8'), Card('H','7'),
                     Card('S','8'), Card('H','10'), Card('C','A'), Card('D','A'), Card('H','K'), Card('S','K'),
                     Card('H','5')]
        sd.add_cards(card_list)
        
        game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = InteractiveCribbagePlayStrategy())
        game._deal._deck = sd
        
        # Player1 will be two point from winning when the game begins, and a pair of A played during first go will end the game
        game._board.peg_for_player1(119)
        return_val = game.play()

        # Did Player1 win?
        exp_val = game._player1
        act_val = return_val.winning_player
        self.assertEqual(exp_val, act_val)

        # Is Player1 score 121?
        exp_val = 121
        act_val = return_val.winning_player_final_score
        self.assertEqual(exp_val, act_val)

        # Has there been only 1 deal?
        exp_val = 1
        act_val = return_val.deals_in_game
        self.assertEqual(exp_val, act_val)


if __name__ == '__main__':
    unittest.main()
