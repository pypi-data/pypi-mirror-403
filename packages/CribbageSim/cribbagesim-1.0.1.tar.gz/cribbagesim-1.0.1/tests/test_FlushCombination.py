# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import FlushCombination

class Test_FlushCombination(unittest.TestCase):
    
    def test_score_flush_hand(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('S','6'), Card('S','J'), Card('S','K')])
        s = Card('H','7')
        fc = FlushCombination()
        info = fc.score(h, s)

        exp_val = 'flush: 1 for 4: 2S 6S JS KS'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
        
    def test_score_flush_starter(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('S','6'), Card('S','J'), Card('S','K')])
        s = Card('S','7')
        fc = FlushCombination()
        info = fc.score(h, s)

        exp_val = 'flush: 1 for 5: 2S 6S JS KS 7S'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)  
    
    def test_score_no_flush(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('D','6'), Card('S','J'), Card('S','K')])
        s = Card('S','7')
        fc = FlushCombination()
        info = fc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)  


if __name__ == '__main__':
    unittest.main()
