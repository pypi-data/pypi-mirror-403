# Standard
import unittest

# Local
from CribbageSim.CribbagePlayStrategy import CribbagePlayStrategy, CribbageCribOption
from CribbageSim.CribbageDeal import CribbageDeal
from HandsDecksCards.card import Card

class Test_CribbagePlayStrategy(unittest.TestCase):
    
    def test_CribbageCribOption_dunder_str(self):
        option = CribbageCribOption()
        option.hand = [Card('S','10'), Card('C','5'), Card('D','10'), Card('H','K')]
        option.hand_score = 8
        option.crib = [Card('H','8'), Card('C','8')]
        option.crib_score = 2
        exp_val = '10S 5C 10D KH,8,8H 8C,2'
        act_val = str(option)
        self.assertEqual(exp_val, act_val)
    
    def test_form_crib(self):

        cd = CribbageDeal()

        cps = CribbagePlayStrategy()
        self.assertRaises(NotImplementedError, cps.form_crib, cd.xfer_player_card_to_crib, cd.get_player_hand)

    def test_follow(self):

        cd = CribbageDeal()

        cps = CribbagePlayStrategy()
        self.assertRaises(NotImplementedError, cps.follow, 0, cd.play_card_for_player, cd.get_player_hand, cd.get_combined_play_pile)

    def test_go(self):

        cd = CribbageDeal()

        cps = CribbagePlayStrategy()
        self.assertRaises(NotImplementedError, cps.go, 0, cd.play_card_for_player, cd.get_player_hand,
                          cd.get_combined_play_pile, cd.determine_score_playing, cd.peg_for_player)
        
    def test_continue_save_end(self):
        
        cps = CribbagePlayStrategy()
        self.assertRaises(NotImplementedError, cps.continue_save_end)


if __name__ == '__main__':
    unittest.main()
