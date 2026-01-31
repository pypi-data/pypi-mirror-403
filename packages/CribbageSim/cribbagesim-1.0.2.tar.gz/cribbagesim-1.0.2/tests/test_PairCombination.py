# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import PairCombination

class Test_PairCombination(unittest.TestCase):
    
    def test_score_with_pairs(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','2'), Card('D','K')])
        s = Card('S','6')
        pc = PairCombination()
        info = pc.score(h, s)

        exp_val = 'pair: 2 for 4: 2S 2H , 6C 6S'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
        
    def test_score_without_pairs(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','A'), Card('D','K')])
        s = Card('S','9')
        pc = PairCombination()
        info = pc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)        



if __name__ == '__main__':
    unittest.main()
