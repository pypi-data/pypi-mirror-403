# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import RunCombination

class Test_RunCombination(unittest.TestCase):
    
    def test_score_run_of_five(self):
        
        h = Hand()
        h.add_cards([Card('S','9'), Card('C','10'), Card('H','Q'), Card('D','K')])
        s = Card('S','J')
        rc = RunCombination()
        info = rc.score(h, s)

        exp_val = 'run: 1 for 5: 9S 10C JS QH KD'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_runs_of_four(self):
        
        h = Hand()
        h.add_cards([Card('S','9'), Card('C','10'), Card('H','Q'), Card('D','10')])
        s = Card('S','J')
        rc = RunCombination()
        info = rc.score(h, s)

        exp_val = 'run: 2 for 8: 9S 10C JS QH , 9S 10D JS QH'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_runs_of_three(self):
        
        h = Hand()
        h.add_cards([Card('S','10'), Card('C','9'), Card('H','9'), Card('D','10')])
        s = Card('S','J')
        rc = RunCombination()
        info = rc.score(h, s)

        exp_val = 'run: 4 for 12: 9C 10S JS , 9H 10S JS , 9C 10D JS , 9H 10D JS'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_without_runs(self):
        
        h = Hand()
        h.add_cards([Card('S','2'), Card('C','6'), Card('H','A'), Card('D','K')])
        s = Card('S','10')
        rc = RunCombination()
        info = rc.score(h, s)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)        



if __name__ == '__main__':
    unittest.main()

