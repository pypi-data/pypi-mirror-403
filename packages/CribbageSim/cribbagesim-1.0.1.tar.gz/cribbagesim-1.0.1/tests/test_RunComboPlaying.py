# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from CribbageSim.CribbageCombination import RunCombinationPlaying

class Test_RunCombinationPlaying(unittest.TestCase):
    
    def test_score_with_run_of_3(self):
        
        pile = Hand()
        pile.add_cards([Card('S','A'), Card('C','J'), Card('H','9'), Card('D','10')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = 'run: 1 for 3: 9H 10D JC'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_run_of_4(self):
        
        pile = Hand()
        pile.add_cards([Card('S','3'), Card('C','6'), Card('H','4'), Card('D','5')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = 'run: 1 for 4: 3S 4H 5D 6C'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_run_of_5(self):
        
        pile = Hand()
        pile.add_cards([Card('S','A'), Card('S','3'), Card('C','6'), Card('H','4'), Card('D','5'), Card('D','7')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = 'run: 1 for 5: 3S 4H 5D 6C 7D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_run_of_6(self):
        
        pile = Hand()
        pile.add_cards([Card('S','3'), Card('C','6'), Card('H','4'), Card('D','5'), Card('D','7'), Card('H','2')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = 'run: 1 for 6: 2H 3S 4H 5D 6C 7D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)

    def test_score_with_run_of_7(self):
        
        pile = Hand()
        pile.add_cards([Card('S','A'), Card('S','3'), Card('C','6'), Card('H','4'), Card('D','5'), Card('D','7'), Card('H','2')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = 'run: 1 for 7: AS 2H 3S 4H 5D 6C 7D'
        act_val = str(info)
        self.assertEqual(exp_val, act_val)
            
    def test_score_without_run(self):
        
        pile = Hand()
        pile.add_cards([Card('S','J'), Card('C','8'), Card('H','Q'), Card('D','K')])
        rcp = RunCombinationPlaying()
        info = rcp.score(pile)

        exp_val = ''
        act_val = str(info)
        self.assertEqual(exp_val, act_val)        


if __name__ == '__main__':
    unittest.main()
