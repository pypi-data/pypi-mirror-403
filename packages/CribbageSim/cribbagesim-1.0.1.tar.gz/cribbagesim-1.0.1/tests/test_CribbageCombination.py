# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import CribbageCombination, CribbageCombinationPlaying, CribbageCombinationShowing

class Test_CribbageCombination(unittest.TestCase):
    
    def test_get_name(self):
        cc = CribbageCombination()
        exp_val = 'none'
        act_val = cc.get_name()
        self.assertEqual(exp_val, act_val)
    
    def test_playing_score(self):
       
        ccp = CribbageCombinationPlaying()
        self.assertRaises(NotImplementedError, ccp.score)

    def test_showing_score(self):
       
        ccs = CribbageCombinationShowing()
        self.assertRaises(NotImplementedError, ccs.score) 
    
    def test_permutations_size_2(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','2'), Card('D','K'), Card('S','6')])
        ccs = CribbageCombinationShowing()
        
        # Create permutations of size 2
        permutations = ccs.permutations(2, h.get_cards())

        # Did we get the expected number of permutations of size 2?
        exp_val = 10
        act_val = len(permutations)
        self.assertEqual(exp_val, act_val)
        
        # Is the first permutation as expected?
        exp_val = ('2', '6')
        act_val = (permutations[0][0].pips, permutations[0][1].pips)
        self.assertEqual(exp_val, act_val)

        # Is the last permutation as expected?
        exp_val = ('K', '6')
        act_val = (permutations[len(permutations)-1][0].pips, permutations[len(permutations)-1][1].pips)
        self.assertTupleEqual(exp_val, act_val)

    def test_permutations_size_5(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','2'), Card('D','K'), Card('S','6')])
        ccs = CribbageCombinationShowing()
        
        # Create permutations of size 5
        permutations = ccs.permutations(5, h.get_cards())

        # Did we get the expected number of permutations of size 5?
        exp_val = 1
        act_val = len(permutations)
        self.assertEqual(exp_val, act_val)
        
        # Is the first (and only) permutation as expected?
        exp_val = ('2', '6', '2', 'K', '6')
        act_val = (permutations[0][0].pips, permutations[0][1].pips, permutations[0][2].pips,
                   permutations[0][3].pips, permutations[0][4].pips)
        self.assertEqual(exp_val, act_val)

    def test_permutations_size_6(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','2'), Card('D','K'), Card('S','6'), Card('C','Q')])
        ccs = CribbageCombinationShowing()
        
        # Try to create permutations of size 5
        self.assertRaises(AssertionError, ccs.permutations, 6, h.get_cards())


if __name__ == '__main__':
    unittest.main()
