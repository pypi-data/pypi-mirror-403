# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import HisNobsCombination

class Test_HisNobsCombination(unittest.TestCase):
    
    def test_score_HisNobs(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('S','6'), Card('H','J'), Card('S','K')])
        s = Card('H','7')
        hnc = HisNobsCombination()
        info = hnc.score(h, s)

        exp_val = 'his nobs: 1 for 1: JH'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
    
    def test_score_no_Jack(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('D','6'), Card('S','Q'), Card('S','K')])
        s = Card('S','7')
        hnc = HisNobsCombination()
        info = hnc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
        
    def test_score_no_suit_match(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('D','6'), Card('H','J'), Card('S','K')])
        s = Card('S','7')
        hnc = HisNobsCombination()
        info = hnc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val) 


if __name__ == '__main__':
    unittest.main()