# Standard
import unittest
from random import seed

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from HandsDecksCards.deck import StackedDeck
from CribbageSim.CribbagePlayStrategy import RandomCribbagePlayStrategy
from CribbageSim.CribbageDeal import CribbageDeal

class Test_RandomCribbagePlayStrategy(unittest.TestCase):
    
    def test_continue_save_end(self):
        rcps = RandomCribbagePlayStrategy()
        act_val = rcps.continue_save_end()
        exp_val = (True, False)
        self.assertEqual(exp_val, act_val)
        
    def test_form_crib(self):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','8'), Card('H','8'), Card('H','K')]
        sd.add_cards(card_list)
        
        deal = CribbageDeal(RandomCribbagePlayStrategy(), RandomCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(6)
        
        rcps = RandomCribbagePlayStrategy()
        
        # Seed the random number generator of the play strategy
        rcps._random_generator.seed(1234567890)

        rcps.form_crib(deal.xfer_player_card_to_crib, deal.get_player_hand)

        # Do we have the expected Card()s in the crib?
        exp_val = [card_list[4], card_list[1]]
        act_val = crib = deal._crib_hand.get_cards()
        self.assertEqual(exp_val, act_val)
        
    def test_follow(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','3'), Card('H','2'), Card('D','4'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling RandomCribbagePlayStrategy.follow(...)
        deal = CribbageDeal(RandomCribbagePlayStrategy(), RandomCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','K'), Card('S','J'), Card('H','6')])
        
        rcps = RandomCribbagePlayStrategy()
        # Seed the random number generator of the play strategy
        rcps._random_generator.seed(1234567890)
        
        # Set go_count to 26, consistent with current play pile
        act_val = rcps.follow(26, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile)        
        
        # Did we get the return value tuple (pip played = 4, go_declared = False)
        exp_val = (4, False)
        self.assertTupleEqual(exp_val, act_val)
        
    def test_go(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','A'), Card('H','3'), Card('D','10'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(RandomCribbagePlayStrategy(), RandomCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','K'), Card('S','J'), Card('H','6')])
        
        rcps = RandomCribbagePlayStrategy()
        # Seed the random number generator of the play strategy
        rcps._random_generator.seed(1234567890)
        
        # Set go_count to 26, consistent with current play pile
        act_val = rcps.go(26, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                          deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of A+3=4?
        exp_val = 4
        self.assertEqual(exp_val, act_val)
        

if __name__ == '__main__':
    unittest.main()
