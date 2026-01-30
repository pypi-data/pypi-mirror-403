# Standard
import unittest

# Local
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand
from HandsDecksCards.deck import StackedDeck
from CribbageSim.CribbagePlayStrategy import HoyleishCribbagePlayStrategy, HoyleishDealerCribbagePlayStrategy, HoyleishPlayerCribbagePlayStrategy
from CribbageSim.CribbageDeal import CribbageDeal


class Test_HoyleishCribbagePlayStrategy(unittest.TestCase):
            
    def test_continue_save_end(self):
        hcp = HoyleishPlayerCribbagePlayStrategy()
        exp_val = (True, False)
        act_val = hcp.continue_save_end()
        self.assertTupleEqual(exp_val, act_val)

    def test_guaranteed_hand_score(self):
        
        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('S','9'), Card('S','9'), Card('S','10'), Card('S','J')])
        
        # 2 runs of 3 for 6, 1 pair for 2, flush for 4, all total = 12
        exp_val = 12
        act_val = hcp.guaranteed_hand_score(h)
        self.assertEqual(exp_val, act_val)

    def test_guaranteed_crib_score_pair(self):
        
        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','9'), Card('S','9')])
        
        # 1 pair for 2
        exp_val = 2
        act_val = hcp.guaranteed_crib_score(h)
        self.assertEqual(exp_val, act_val)

    def test_guaranteed_crib_score_15(self):
        
        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('H','7'), Card('S','8')])
        
        # 1 fifteen for 2
        exp_val = 2
        act_val = hcp.guaranteed_crib_score(h)
        self.assertEqual(exp_val, act_val)

    def test_guaranteed_crib_score_none(self):
        
        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('H','7'), Card('S','K')])
        
        exp_val = 0
        act_val = hcp.guaranteed_crib_score(h)
        self.assertEqual(exp_val, act_val)

    def test_permute_and_score_dealt_hand(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','9'), Card('S','9'), Card('S','10'), Card('S','J'), Card('H','2'), Card('D','2')])

        options_list = hcp.permute_and_score_dealt_hand(h.get_cards())

        # Did we get the expected number of options?
        exp_val = 15
        act_val = len(options_list)
        self.assertEqual(exp_val, act_val)

        # Does the first option have the expected hand score?
        # 2 runs of 3 for 6, 1 pair for 2, all total = 8
        exp_val = 8
        act_val = options_list[0].hand_score
        self.assertEqual(exp_val, act_val)

        # Does the first option have the expected hand Card()s?
        exp_val = h.get_cards()[0:4]
        act_val = options_list[0].hand
        self.assertEqual(exp_val, act_val)

        # Does the first option have the expected crib score?
        # 1 pair (of 2's) for 2
        exp_val = 2
        act_val = options_list[0].crib_score
        self.assertEqual(exp_val, act_val)

        # Does the first option have the expectee crib Card()s?
        exp_val = h.get_cards()[4:6]
        act_val = options_list[0].crib
        self.assertEqual(exp_val, act_val)

    # Name of test based on leading to potentially capture a triplet
    def test_rate_leads_in_hand_triplets(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','A'), Card('S','A'), Card('H','2'), Card('D','2'), Card('S','3'), Card('C','3'), Card('D','4'), Card('H','4'),
                     Card('C','5'), Card('S','5'), Card('H','6'), Card('D','6'), Card('S','7'), Card('C','7'), Card('D','8'), Card('H','8'),
                     Card('C','9'), Card('S','9'), Card('H','10'), Card('D','10'), Card('S','J'), Card('C','J'), Card('D','Q'), Card('H','Q'),
                     Card('C','K'), Card('S','K')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 26
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(22, ratings_list[0][1]) # 'A':22
        self.assertEqual(22, ratings_list[1][1]) # 'A':22
        self.assertEqual(23, ratings_list[2][1]) # '2':23
        self.assertEqual(23, ratings_list[3][1]) # '2':23
        self.assertEqual(24, ratings_list[4][1]) # '3':24
        self.assertEqual(24, ratings_list[5][1]) # '3':24
        self.assertEqual(25, ratings_list[6][1]) # '4':25
        self.assertEqual(25, ratings_list[7][1]) # '4':25
        self.assertEqual(0, ratings_list[8][1]) # '5':0
        self.assertEqual(0, ratings_list[9][1]) # '5':0
        self.assertEqual(17, ratings_list[10][1]) # '6':17
        self.assertEqual(17, ratings_list[11][1]) # '6':17
        self.assertEqual(18, ratings_list[12][1]) # '7':18
        self.assertEqual(18, ratings_list[13][1]) # '7':18
        self.assertEqual(19, ratings_list[14][1]) # '8':19
        self.assertEqual(19, ratings_list[15][1]) # '8':19
        self.assertEqual(20, ratings_list[16][1]) # '9':10
        self.assertEqual(20, ratings_list[17][1]) # '9':10
        self.assertEqual(21, ratings_list[18][1]) # '10':21
        self.assertEqual(21, ratings_list[19][1]) # '10':21
        self.assertEqual(21, ratings_list[20][1]) # 'J':21
        self.assertEqual(21, ratings_list[21][1]) # 'J':21
        self.assertEqual(21, ratings_list[22][1]) # 'Q':21
        self.assertEqual(21, ratings_list[23][1]) # 'Q':21
        self.assertEqual(21, ratings_list[24][1]) # 'K':21
        self.assertEqual(21, ratings_list[25][1]) # 'K':21

    # Name of test based on leading to potentially capture a run (6-7-8 or 7-8-9) or a pair (9s or 6s)
    def test_rate_leads_in_hand_runspairs(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','6'), Card('S','7'), Card('H','8'), Card('D','9')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 4
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(10, ratings_list[0][1]) # '6':10
        self.assertEqual(15, ratings_list[1][1]) # '7':15
        self.assertEqual(16, ratings_list[2][1]) # '8':16
        self.assertEqual(13, ratings_list[3][1]) # '9':13
    
    # Name of test based on leading to potentially capture a pair (7s or 8s)
    def test_rate_leads_in_hand_pairs(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('S','7'), Card('H','8')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 2
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(11, ratings_list[0][1]) # '7':11
        self.assertEqual(12, ratings_list[1][1]) # '8':12

    # Name of test based on leading to potentially capture a pair of 5s
    def test_rate_leads_in_hand_pair5s(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','5'), Card('H','10'), Card('S','J'), Card('H','Q'), Card('C','K')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 5
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(0, ratings_list[0][1]) # '5':0
        self.assertEqual(14, ratings_list[1][1]) # '10':0
        self.assertEqual(14, ratings_list[2][1]) # 'J':14
        self.assertEqual(14, ratings_list[3][1]) # 'Q':14
        self.assertEqual(14, ratings_list[4][1]) # 'K':14


    def test_rate_leads_in_hand_singletons_A123456(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','A'), Card('S','2'), Card('S','3'), Card('S','4'), Card('H','5'), Card('D','6')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 6
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(6, ratings_list[0][1]) # 'A':6
        self.assertEqual(7, ratings_list[1][1]) # '2':7
        self.assertEqual(8, ratings_list[2][1]) # '3':8
        self.assertEqual(9, ratings_list[3][1]) # '4':9
        self.assertEqual(0, ratings_list[4][1]) # '5':0
        self.assertEqual(1, ratings_list[5][1]) # '6':1

    def test_rate_leads_in_hand_singletons_910JQK(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','9'), Card('S','10'), Card('H','J'), Card('D','Q'), Card('C','K')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 5
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(4, ratings_list[0][1]) # '9':4
        self.assertEqual(5, ratings_list[1][1]) # '10':5
        self.assertEqual(5, ratings_list[2][1]) # '7':5
        self.assertEqual(5, ratings_list[3][1]) # 'Q':5
        self.assertEqual(5, ratings_list[4][1]) # 'K':5

    def test_rate_leads_in_hand_singletons_7(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','7')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 1
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(2, ratings_list[0][1]) # '7':2

    def test_rate_leads_in_hand_singletons_8(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','8')])

        ratings_list = hcp.rate_leads_in_hand(h)

        # Did we get one rating for each card in the hand?
        exp_val = 1
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # 'pips':rating
        self.assertEqual(3, ratings_list[0][1]) # '8':3

    def test_rate_follows_in_hand_31(self):
        hcp = HoyleishCribbagePlayStrategy()

        hand = Hand()
        hand.add_cards([Card('C','A'), Card('H','2'), Card('D','3'), Card('S','3')])
        
        pile = Hand()
        pile.add_cards([Card('C','K'), Card('H','10'), Card('S','8')])
        
        ratings_list = hcp.rate_follows_in_hand(hand, pile)

        # Did we get one rating for each card in the hand?
        exp_val = 4
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # card:rating (why)
        self.assertEqual(0, ratings_list[0][1]) # AC:0
        self.assertEqual(0, ratings_list[1][1]) # 2H:0
        self.assertEqual(2, ratings_list[2][1]) # 3D:2 (31)
        self.assertEqual(2, ratings_list[3][1]) # 3S:2 (31)

    def test_rate_follows_in_hand_15_triplet(self):
        hcp = HoyleishCribbagePlayStrategy()

        hand = Hand()
        hand.add_cards([Card('C','A'), Card('H','9'), Card('D','3'), Card('S','6')])
        
        pile = Hand()
        pile.add_cards([Card('C','3'), Card('S','3')])
        
        ratings_list = hcp.rate_follows_in_hand(hand, pile)

        # Did we get one rating for each card in the hand?
        exp_val = 4
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # card:rating (why)
        self.assertEqual(0, ratings_list[0][1]) # AC:0
        self.assertEqual(2, ratings_list[1][1]) # 9H:2 (15)
        self.assertEqual(6, ratings_list[2][1]) # 3D:6 (triplet)
        self.assertEqual(0, ratings_list[3][1]) # 6S:0

    def test_rate_follows_in_hand_run_15_pair(self):
        hcp = HoyleishCribbagePlayStrategy()

        hand = Hand()
        hand.add_cards([Card('C','A'), Card('H','K'), Card('D','3'), Card('S','6')])
        
        pile = Hand()
        pile.add_cards([Card('C','2'), Card('S','3')])
        
        ratings_list = hcp.rate_follows_in_hand(hand, pile)

        # Did we get one rating for each card in the hand?
        exp_val = 4
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # card:rating (why)
        self.assertEqual(3, ratings_list[0][1]) # AC:3 (run of 3)
        self.assertEqual(2, ratings_list[1][1]) # KH:2 (15)
        self.assertEqual(2, ratings_list[2][1]) # 3D:2 (pair)
        self.assertEqual(0, ratings_list[3][1]) # 6S:0

    def test_rate_follows_in_hand_no_play_score(self):
        hcp = HoyleishCribbagePlayStrategy()

        hand = Hand()
        hand.add_cards([Card('C','9'), Card('H','K'), Card('D','3'), Card('S','6')])
        
        pile = Hand()
        pile.add_cards([Card('C','A'), Card('S','A')])
        
        ratings_list = hcp.rate_follows_in_hand(hand, pile)

        # Did we get one rating for each card in the hand?
        exp_val = 4
        act_val = len(ratings_list)
        self.assertEqual(exp_val, act_val)

        # Did the cards get rated as expected?
        # Format: self.assertEqual(exp_val, act_val) # card:rating (why)
        self.assertEqual(9, ratings_list[0][1]) # 9C:9 (pip)
        self.assertEqual(10, ratings_list[1][1]) # KH:10 (pip)
        self.assertEqual(3, ratings_list[2][1]) # 3D:3 (pip)
        self.assertEqual(6, ratings_list[3][1]) # 6S:6 (pip)

        
    def test_follow_no_playable_card(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','3')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.follow(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 29 so that no cards are playable, and GO is declared
        act_val = hcp.follow(29, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile)        
        
        # Did we get the return value tuple (pip played = 0, go_declared = True)
        exp_val = (0, True)
        self.assertTupleEqual(exp_val, act_val)

    def test_follow_lead(self):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('S','10'), Card('C','5'), Card('D','A'), Card('C','3')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.follow(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 0, consistent with leading, but the lead will happen because combined play pile is empty
        act_val = hcp.follow(0, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile)        
        
        # Did we get the return value tuple (pip played = 10, go_declared = False)
        exp_val = (10, False)
        self.assertTupleEqual(exp_val, act_val)

    def test_lead_1(self):

        hcp = HoyleishCribbagePlayStrategy()
        
        h = Hand()
        h.add_cards([Card('C','6'), Card('D','7'), Card('H','8'), Card('S','9')])

        # Does the 8H get lead as expected?
        exp_val = (8, h[2])
        act_val = hcp.lead(h)
        self.assertTupleEqual(exp_val, act_val)

    def test_follow_play_score(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','A'), Card('H','9'), Card('D','3'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.follow(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','3'), Card('S','3')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 6, consistent with current play pile
        act_val = hcp.follow(6, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile)        
        
        # Did we get the return value tuple (pip played = 3, go_declared = False)
        exp_val = (3, False)
        self.assertTupleEqual(exp_val, act_val)

    def test_follow_play_highest_playable(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','3'), Card('H','2'), Card('D','4'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.follow(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','K'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 26, consistent with current play pile
        act_val = hcp.follow(26, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile)        
        
        # Did we get the return value tuple (pip played = 4, go_declared = False)
        exp_val = (4, False)
        self.assertTupleEqual(exp_val, act_val)

    def test_go_to_30(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','A'), Card('H','3'), Card('D','10'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','K'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 26, consistent with current play pile
        act_val = hcp.go(26, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                         deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of A+3=4?
        exp_val = 4
        self.assertEqual(exp_val, act_val)

    def test_go_to_31(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','2'), Card('H','3'), Card('D','10'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','K'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 26, consistent with current play pile
        act_val = hcp.go(26, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                         deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of 2+3=5?
        exp_val = 5
        self.assertEqual(exp_val, act_val)

    def test_go_pair_bug(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','2'), Card('H','3'), Card('D','7'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','8'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 24, consistent with current play pile
        act_val = hcp.go(24, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                         deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of 6?
        exp_val = 6
        self.assertEqual(exp_val, act_val)

    def test_go_pair(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','2'), Card('H','3'), Card('D','8'), Card('S','6')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','8'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 24, consistent with current play pile
        act_val = hcp.go(24, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                         deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of 6?
        exp_val = 6
        self.assertEqual(exp_val, act_val)

    def test_go_no_play(self):
        # go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback):
        
        # Create a stacked deck
        sd = StackedDeck()
        # Cards 1 - 4 will be drawn into player's hand
        card_list = [Card('C','8'), Card('H','9'), Card('D','10'), Card('S','8')]
        sd.add_cards(card_list)
        
        # Create a CribbageDeal, which for this test, will provide the callback functions for calling HoyleishCribbagePlayStrategy.go(...)
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(4)

        # Create a combined play pile for the deal
        deal._combined_pile.add_cards([Card('C','8'), Card('S','J'), Card('H','6')])
        
        hcp = HoyleishCribbagePlayStrategy()
        # Set go_count to 24, consistent with current play pile
        act_val = hcp.go(24, deal.play_card_for_player, deal.get_player_hand, deal.get_combined_play_pile,
                         deal.determine_score_playing, deal.peg_for_player)        
        
        # Did we get the return play count expected of 0?
        exp_val = 0
        self.assertEqual(exp_val, act_val)

    def test_dealer_form_crib_max_hand(self):

        # Create a stacked deck
        sd = StackedDeck()
        # Dealer will be dealt cards 1 - 6
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','3'), Card('H','8'), Card('H','K')]
        sd.add_cards(card_list)
        
        deal = CribbageDeal(HoyleishDealerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_dealer(6)
        
        hcp = HoyleishDealerCribbagePlayStrategy()
        hcp.form_crib(deal.xfer_dealer_card_to_crib, deal.get_dealer_hand)

        # Do we have the expected first card in the crib?
        crib = deal._crib_hand.get_cards()
        exp_val = ('C', '3')
        act_val = (crib[0].suit, crib[0].pips)
        self.assertTupleEqual(exp_val, act_val)

        # Do we have the expected second card in the crib?
        crib = deal._crib_hand.get_cards()
        exp_val = ('H', '8')
        act_val = (crib[1].suit, crib[1].pips)
        self.assertTupleEqual(exp_val, act_val)

    def test_dealer_form_crib_max_hand_crib(self):

         # Create a stacked deck
        sd = StackedDeck()
        # Dealer will be dealt cards 1 - 6
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','8'), Card('H','8'), Card('H','K')]
        sd.add_cards(card_list)
        
        deal = CribbageDeal(HoyleishDealerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_dealer(6)
        
        hcp = HoyleishDealerCribbagePlayStrategy()
        hcp.form_crib(deal.xfer_dealer_card_to_crib, deal.get_dealer_hand)

        # Do we have the expected first card in the crib?
        crib = deal._crib_hand.get_cards()
        exp_val = ('C', '8')
        act_val = (crib[0].suit, crib[0].pips)
        self.assertTupleEqual(exp_val, act_val)

        # Do we have the expected second card in the crib?
        crib = deal._crib_hand.get_cards()
        exp_val = ('H', '8')
        act_val = (crib[1].suit, crib[1].pips)
        self.assertTupleEqual(exp_val, act_val)

    def test_player_form_crib_max_hand_less_crib(self):

         # Create a stacked deck
        sd = StackedDeck()
        # Player will be dealt cards 1 - 6
        card_list = [Card('S','10'), Card('C','5'), Card('D','10'), Card('C','8'), Card('H','8'), Card('H','K')]
        sd.add_cards(card_list)
        
        deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
        deal._deck = sd
        deal.draw_for_player(6)
        
        hcp = HoyleishPlayerCribbagePlayStrategy()
        hcp.form_crib(deal.xfer_player_card_to_crib, deal.get_player_hand)

        # Do we have the expected Card()s in the crib?
        exp_val = [card_list[4], card_list[5]]
        act_val = crib = deal._crib_hand.get_cards()
        self.assertEqual(exp_val, act_val)
        

if __name__ == '__main__':
    unittest.main()
