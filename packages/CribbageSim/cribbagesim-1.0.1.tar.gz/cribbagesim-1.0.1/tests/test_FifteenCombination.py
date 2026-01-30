# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards. import Hand
from CribbageCombination import FifteenCombination

class Test_FifteenCombination(unittest.TestCase):
    
    def test_score_with_two_card_fifteens(self):
        
        h = Hand()
        h.add_cards([Card('S','9'), Card('C','6'), Card('H','2'), Card('D','K')])
        s = Card('S','6')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = 'fifteen: 2 for 4: 9S 6C , 9S 6S'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_three_card_fifteens(self):
        
        h = Hand()
        h.add_cards([Card('S','K'), Card('C','2'), Card('H','3'), Card('D','Q')])
        s = Card('S','7')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = 'fifteen: 2 for 4: KS 2C 3H , 2C 3H QD'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
        
    def test_score_with_four_card_fifteens(self):
        
        h = Hand()
        h.add_cards([Card('S','K'), Card('C','2'), Card('H','2'), Card('D','A')])
        s = Card('S','10')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = 'fifteen: 2 for 4: KS 2C 2H AD , 2C 2H AD 10S'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
            
    def test_score_with_five_card_fifteen(self):
        
        h = Hand()
        h.add_cards([Card('S','K'), Card('C','2'), Card('H','A'), Card('D','A')])
        s = Card('S','A')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = 'fifteen: 1 for 2: KS 2C AH AD AS'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_two_and_three_card_fifteens(self):
        
        h = Hand()
        h.add_cards([Card('S','K'), Card('C','5'), Card('H','2'), Card('D','3')])
        s = Card('S','A')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = 'fifteen: 2 for 4: KS 5C , KS 2H 3D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_without_fifteens(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','A'), Card('D','K')])
        s = Card('S','10')
        fc = FifteenCombination()
        info = fc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)        



if __name__ == '__main__':
    unittest.main()

