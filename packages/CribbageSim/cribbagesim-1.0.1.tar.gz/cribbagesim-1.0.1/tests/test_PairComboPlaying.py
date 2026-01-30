# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import PairCombinationPlaying

class Test_PairCombinationPlaying(unittest.TestCase):
    
    def test_score_with_double_pair_royal(self):
        
        pile = Hand()
        pile.add_cards([Card('D','J'), Card('S','2'), Card('C','2'), Card('H','2'), Card('D','2')])
        pcp = PairCombinationPlaying()
        info = pcp.score(pile)

        exp_val = 'double pair royal: 1 for 12: 2S 2C 2H 2D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
    
    def test_score_with_pair_royal(self):
        
        pile = Hand()
        pile.add_cards([Card('D','J'), Card('S','4'), Card('C','2'), Card('H','2'), Card('D','2')])
        pcp = PairCombinationPlaying()
        info = pcp.score(pile)

        exp_val = 'pair royal: 1 for 6: 2C 2H 2D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_pair(self):
        
        pile = Hand()
        pile.add_cards([Card('D','J'), Card('S','4'), Card('C','3'), Card('H','2'), Card('D','2')])
        pcp = PairCombinationPlaying()
        info = pcp.score(pile)

        exp_val = 'pair: 1 for 2: 2H 2D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
        
    def test_score_without_pairs(self):
        
        pile = Hand()
        pile.add_cards([Card('S','2'), Card('C','6'), Card('H','A'), Card('D','K')])
        pcp = PairCombinationPlaying()
        info = pcp.score(pile)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)        


if __name__ == '__main__':
    unittest.main()
