# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import FifteenCombinationPlaying

class Test_FifteenCombinationPlaying(unittest.TestCase):
    
    def test_score_with_fifteen(self):
        
        pile = Hand()
        pile.add_cards([Card('D','J'), Card('S','2'), Card('C','3')])
        fcp = FifteenCombinationPlaying()
        info = fcp.score(pile)

        exp_val = 'fifteen: 1 for 2: JD 2S 3C'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
           
    def test_score_without_fifteen(self):
        
        pile = Hand()
        pile.add_cards([Card('D','J'), Card('S','2'), Card('C','4')])
        fcp = FifteenCombinationPlaying()
        info = fcp.score(pile)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)


if __name__ == '__main__':
    unittest.main()