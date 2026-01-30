"""
This moduel defines playing strategies for cribbage games, by defining the abstract base class CribbagePlayStrategy,
which follows a Strategy design pattern. It also defines several concrete child implementations.

Concrete implementation child classes must:
    (1) Implement the method form_crib(...) for selecting two cards from the dealt six to be placed in the crib.
    (2) Implement the method follow(...) for selecting cards to play after the lead, up until a declaration of "go" by opponent.
    (3) Implement the method go(...) for playing out as many cards as possible after the opponent has declared "go".
    (4) Implement the method continue_save_end(...) for deciding whether to continue playing another deal, saving the
        game state and ending the game, or ending the game without saving the game state.
Concrete implementation child classes may:
    (5) Provide an __init__(...) to initialize any required attributes, for example.

Exported Classes:
    CribbageCribOption - Attributes are structured information about possible options for forming a crib.
                         Used by HoyleishXCribbagePlayStrategy class methods.
    CribbagePlayStrategy - Following a Strategy design pattern, this is the interface class for all cribbage hand playing strategies.
    HoyleishCribbagePlayStrategy - Base class for dealer and player play strategies based initially/roughly on "Strategy for Cribbage" described in Hoyle.
    HoyleishDealerCribbagePlayStrategy - Dealer implementation of form_crib(...) method allows for dealer to place points in the crib.
    HoyleishPlayerCribbagePlayStrategy - Player implementation of form_crib(...) method typically avoids the player placing points in the crib.
    InteractiveCribbagePlayStrategy - Strategy for a human player, where the user is consulted for playing choices.
    RandomCribbagePlayStrategy - CribbagePlayStrategy that simply chooses randomly from hand to form crib, and randomly from playable cards to follow or go.

Exported Exceptions:
    None    
 
Exported Functions:
    None

Logging:
    None
"""


# Standard imports
import random

# Local imports
import UserResponseCollector.UserQueryReceiver # Leave this like it is, so that import can be used to do a swap out of the UserQueryReceiver between base and child if needed
from UserResponseCollector.UserQueryCommand import UserQueryCommandMenu
from CribbageSim.CribbageCombination import CribbageCombinationShowing, PairCombination, FifteenCombination, RunCombination, FlushCombination
from CribbageSim.CribbageCombination import CribbageCombinationPlaying, PairCombinationPlaying, FifteenCombinationPlaying, RunCombinationPlaying
from HandsDecksCards.hand import Hand
from CribbageSim.exceptions import CribbageGameOverError


class CribbageCribOption:
    """
    A class with structured information about a possible option for forming the crib. All class attributes are intended to be "public".
        hand: List of 4 cards to be retained in the hand if a crib is formed using this option, list of Card objects
        hand_score: The guaranteed score of the cards in the hand when the hand is shown, that is, the score of the cards without
            consideration of a possible starter card, int
        crib: List of 2 cards to be layed in teh crib if a crib is formed using this option, list of Card objects
        crib_score: The guaranteed score of the two cards in the crib when the crib is shown, that is, the score of the cards without
            consideration of a possible starter card or the other player's contribution to the crib, int
    """
    def __init__(self):
        """
        Construct an object of this class.
        """
        self.hand = []
        self.hand_score = 0
        self.crb = []
        self.crib_score = 0

    def __str__(self):
        hand = Hand()
        hand.add_cards(self.hand)
        crib = Hand()
        crib.add_cards(self.crib)
        return f"{hand},{self.hand_score},{crib},{self.crib_score}"


class CribbagePlayStrategy:
    """
    Following a Strategy design pattern, this is the interface class for all cribbage hand playing strategies.
    Each child must by convention and necessity implement these methods:
        form_crib(...) - For selecting two cards from the dealt six to be placed in the crib 
        follow(...) - For selecting subsequent cards to play seeking finally a "go". This logic will depend on all cards played so far during
            the current "go" round by both dealer and player. Could also depend on how close to done the game is, since when a player is a few
            pegs from winning and the game is close, scoring during play may be more valualbe than getting a high count during show.
        go(...) - For playing out as many cards as possible AFTER opponent has declared "go".
        continue_save_end(...) - For deciding weether to continue by playing another deal, saving the game state and ending, or ending without
            saving the game state.
    """
    def form_crib(self, xfer_to_crib_callback, get_hand_callback, play_recorder_callback=None):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        Called to decide which cards from the hand to place in the crib.
        :parameter xfer_to_crib_callback: Bound method used to transfer cards from hand to crib, e.g., CribbageDeal.xfer_player_card_to_crib
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: None
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(xfer_to_crib_callback))
        assert(callable(get_hand_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        raise NotImplementedError
        return None

    def follow(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, play_recorder_callback=None):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        Called to decide which card to follow (play) in a go round.
        :parameter go_count: The current cumulative count of the go round before the follow, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: (The pips count of the card played as int, Go declared as boolean), tuple
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        raise NotImplementedError
        return ('10', False)

    def go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback,
           play_recorder_callback=None):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        Determine which card(s) if any to play in a go round after opponent has declared go.
        :parameter go_count: The current cumulative count of the go round that caused opponent to declare go, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter score_play_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.determine_score_playing
        :parameter peg_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.peg_for_player
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: The sum of pips count of any cards played, int
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(score_play_callback))
        assert(callable(peg_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        raise NotImplementedError
        return 0

    def continue_save_end(self):
        """
        This is an abstract method that must be implemented by children. If called, it will raise NotImplementedError.
        Determine if game play should continue by proceeding to the next deal, if current game state should be saved and game play ended,
        or if game play should be ended without saving current game state.
        :return: Tuple (Continue Game True/False, Save Game State True/False). If first tuple value is True, second tuple value should be ignored.
        """
        raise NotImplementedError
        return (False, False)


# Note: For Hoyleish play strategy, Will need separate implementations for dealer and player, since form_crib(...) logic will be different for each.

class HoyleishCribbagePlayStrategy(CribbagePlayStrategy):
    """
    Base class for dealer and player play strategies based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish"
    implies that not all recommendations from Hoyle may be implemented, and other strategy components may be implemented alternatively or
    in addition too.
    """
    def __init__(self):
        """
        Construct an object of this class.
        """
        # All elements of the _guaranteed_4card_combinations and _guaranteed_2card_combinations lists must be children of
        # CribbageCombinationShowing class.
        self._guaranteed_4card_combinations = [PairCombination(), FifteenCombination(), RunCombination(), FlushCombination()]
        self._guaranteed_2card_combinations = [PairCombination(), FifteenCombination()]
        # All elements of the _play_combinations list must be children of CribbageCombinationPlaying class.
        self._play_combinations = [FifteenCombinationPlaying(), PairCombinationPlaying(), RunCombinationPlaying()]
 
    def follow(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, play_recorder_callback=None):
        """
        Follows (plays) a card based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations
        from Hoyle may be implemented, and other strategy components may be implemented alternatively or in addition too.
        :parameter go_count: The current cumulative count of the go round before the follow, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: (The pips count of the card played as int, Go declared as boolean), tuple
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        
        # Default tuple to return, arbitrarily here a GO tuple, but expected to be set in all branches below
        return_val = (0, True)
        
        # Determine list of cards in the hand that can be played without go_count exceeding 31.
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - go_count)]

        if len(playable) > 0:
            if len(get_play_pile_callback()) == 0:
                # The play pile has no cards in it, so this is a lead, so call lead(...) method
                h = Hand()
                h.add_cards(playable)
                (count, card) = self.lead(h)
                play_card_callback(get_hand_callback().index(card))
                return_val = (count, False)
            else:
                # Apply logic for following
                hand = Hand()
                hand.add_cards(playable)
                pile = Hand()
                pile.add_cards(get_play_pile_callback())
                priority_list = self.rate_follows_in_hand(hand, pile)
                # Sort priority_list by descending rating
                sorted_list = sorted(priority_list, key = lambda rating: rating[1], reverse = True)
                card = sorted_list[0][0]
                count = card.count_card()
                play_card_callback(get_hand_callback().index(card))
                return_val = (count, False)
                
        else:
            # If no cards in the hand can be played, then return (0, True), in other words, declare GO.
            return (0, True) 

        return return_val

    def go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback,
           play_recorder_callback=None):
        """
        Determines which card(s) if any to play in a go round after opponent has declared go. Determination based initially/roughly on
        "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations from Hoyle may be implemented,
        and other strategy components may be implemented alternatively or in addition too.
        :parameter go_count: The current cumulative count of the go round that caused opponent to declare go, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter score_play_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.determine_score_playing
        :parameter peg_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.peg_for_player
        :parameter play_recorder_callback: Bound method used to record user choices for cards to play during the go
        :return: The sum of pips count of any cards played, int
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        assert(callable(score_play_callback))
        assert(callable(peg_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # The overall process flow in this function is the same as for 

        play_count = go_count
        
        # Generate list of which if any cards can still be played
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]

        while (len(playable) > 0):

            # Determine which card to play

            # TODO: Logic here optimally would be conceptually that we would permute (including different orderings) all possible play sequences
            # of playable cards that together make the play pile sum to <= 31. Each of these play sequences would be scored one card in the
            # sequence at a time, and the total over the play sequence would be a priority weight for choosing that play sequence

            # For now though, we'll consider it close enough to optimize each individual choice of playable cards, one at a time,
            # and we will use rate_follows_in_hand() method to do so
            hand = Hand()
            hand.add_cards(playable)
            pile = Hand()
            pile.add_cards(get_play_pile_callback())
            priority_list = self.rate_follows_in_hand(hand, pile)
            # Sort priority_list by descending rating
            sorted_list = sorted(priority_list, key = lambda rating: rating[1], reverse = True)
            card = sorted_list[0][0]
            count = card.count_card()

            # TODO: Fix issue that if a card can be played during go that would make a pair, and a different card can be played that would make 31,
            # that which of those gets played depends on the order of the cards in the hand. Optimally, the pair should be played to collect the 2
            # for the pair plus 1 for the go.

            # Play card
            play_card_callback(get_hand_callback().index(card))
            play_count += count

            # Score any pairs or runs due to the played card
            reasons = []
            score_count = score_play_callback(get_play_pile_callback(), score_reasons=reasons)
            try:
                peg_callback(score_count, reasons)
            except CribbageGameOverError as e:
                # (except covered by unit test)
                # Raise a new CribbageGameOverError with the added information about score during play
                raise CribbageGameOverError(e.args, go_play_score = score_count)

            # Generate list of which if any cards can still be played
            playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]
        
        return (play_count - go_count)
    
    def continue_save_end(self):
        """
        Determine if game play should continue by proceeding to the next deal, if current game state should be saved and game play ended,
        or if game play should be ended without saving current game state. Since this strategy is for automatic play (i.e., for a machine player),
        answer will always be to continue the game.
        :return: Tuple (Continue Game True/False, Save Game State True/False). If first tuple value is True, second tuple value should be ignored.
        """
        return (True, False)

    def lead(self, hand = Hand()):
        """
        Leads (plays) a first card in a go round based initially/roughly on "Strategy for Cribbage" described in Hoyle.
        The "ish" implies that not all recommendations from Hoyle may be implemented, and other strategy components may be implemented
        alternatively or in addition too. This is a utility method intended to be called by follow(...) method, not by outsiders.
        :parameter hand: The hand from which to lead a card, Hand object
        :return: Tuple of (The pips count of the card to be led, The card to be led) (int, Card object) 
        """

        priority_list = self.rate_leads_in_hand(hand)

        # Sort priority_list by descending rating
        sorted_list = sorted(priority_list, key = lambda rating: rating[1], reverse = True)

        # Return the top-rated card as the lead
        lead_card = sorted_list[0][0]
        lead_count = lead_card.count_card()
        
        return (lead_count, lead_card)

    def guaranteed_hand_score(self, hand = Hand()):
        """
        Utility function that determines the show points with 100% expectation in a cribbage hand. For example, a pair is counted, but a His Nobs
        is NOT counted, because it depends on the suit of the starter, and thus would be considered to have an
        expected value of 1 pnt X 0.25 prob = 0.25 points.
        :parameter hand: The cards to score, Hand object
        :return: Total points in the hand that have 100% expectation of being counted, int
        """
        score = 0
        for combo in self._guaranteed_4card_combinations:
            assert(isinstance(combo, CribbageCombinationShowing))
            info = combo.score(hand)
            score += info.score
        return score

    def guaranteed_crib_score(self, crib = Hand()):
        """
        Utility function that determines the show points with 100% expectation in a cribbage crib contribution of 2 cards.
        For example, a pair is counted, but a His Nobs is NOT counted, because it depends on the suit of the starter, and thus would be considered to have an
        expected value of 1 pnt X 0.25 prob = 0.25 points.
        :parameter hand: The cards to score, Hand object
        :return: Total points in the crib from the 2-card contribution that have 100% expectation of being counted, int
        """
        score = 0
        for combo in self._guaranteed_2card_combinations:
            assert(isinstance(combo, CribbageCombinationShowing))
            info = combo.score(crib)
            score += info.score
        return score

    def permute_and_score_dealt_hand(self, hand = Hand()):
        """
        Utility function that permutes the dealt hand of six cards for all combinations of four cards, scores the four cards in the hand
        for each permutation, and scores teh two cards in the crib for each permutation.
        :parameter hand: The six cards to permute and score, Hand object
        :return: A list of CribbageCribOption instance with hand, crib, and scores for each permutation, list of CribbageCribOption object
        """
        assert(len(hand) == 6)
        
        # Get the cards in the hand, twice, so we have two lists that (for the moment) are duplicates
        cards_1 = list(hand)
        
        # Need a CribbageCombinationShowing() object, to access it's permutations utility method
        permutations = CribbageCombinationShowing().permutations(4, cards_1)

        # Score each permutation and make a list of tuples (list of cards, score)
        priority_list = []
        for p in permutations:
            crib_option = CribbageCribOption()
            crib_option.hand = p
            h = Hand()
            h.add_cards(p)
            p_score = self.guaranteed_hand_score(h)
            crib_option.hand_score = p_score
            priority_list.append(crib_option)
            # Generate the list of cards to be placed in the crib for permutation p, by removing cards from hand
            cards_2 = list(hand)
            for c in p:
                cards_2.remove(c)
            h = Hand()
            h.add_cards(cards_2)
            p_score = self.guaranteed_crib_score(h)
            crib_option.crib_score = p_score
            crib_option.crib = cards_2

        return priority_list

    def rate_leads_in_hand(self, hand = Hand()):
        """
        Utility function that provides a "rating" or arbitrary "score" for each card in the hand. The rating is chosen such that
        the card with the highest rating is the card that is considered a better lead, meaning that it is more likely to generate more play
        points for the leader and generate less play points for the opponent.
        :parameter hand: The hand of cards fro which to generate ratings, Hand object
        :return: List of tuples (Card, Rating), [(Card object, int)]
        """
        # Basis for ratings: Apply this list in a "greedy" fashion from top to bottom. That is, if a card recives a rating from a scenario
        # higher in the list, do not apply a lower scenario to it. See also Developer_Documentation.txt for though process that led to this list.
        # (1) If you have any pair but 5's in your hand, lead one of them, hoping to capture a triplet for 6. If you lead from a pair of 5's
        # most likely the opponent will capture a 15 by plaing a 10/face, and you will capture nothing.
        #   {Rate both cards of a pair as follows 6X:17,7X:18,8X:19,9X:20,10X/Face:21,A:22,2X23,3X24,4X:25}
        # (2) If you have a 6 and an 8 in your hand, lead the 8, hoping to capture a run of 3 with the 6.
        #   {Rate an 8 in this situation as a 16}
        # (3) If you have a 7 and 9 in your hand, lead the 7, hoping to capture a run of 3 with the 9.
        #   {Rate a 7 in this situation as a 15}
        # (4) If you have a 5 and a 10/face in your hand, lead the 10/face, hoping to capture a pair with the 5.
        #   {Rate each 10/Face in this situation as 14}
        # (5) If you have a 6-9 or a 7-8 in your hand, lead one of them, hoping to capture a pair with the other.
        #   {Rate a 6, 7, 8, or 9 in this situation as 10, 11, 12, 13 respectively, so that also take advantage of (7)}
        # (6) Lead any card in your hand less than 5, to defend against a 15. With preference running 4 > 3 > 2 > A
        #   {Rate A as 6, 2 as 7, 3 as 8, 4 as 9}
        # (7) Lead any card greater than 5 in your hand. With preference running Face/10 > 9 > 8 > 7 > 6.
        #   {Rate: 6 as 1, 7 as 2, 8 as 3, 9 as 4, 10/Face as 5}
        # (8) Very last option would be to lead a 5. {rate a 5 as 0}

        pair_ratings_map = {'5':0, '6':17, '7':18, '8':19, '9':20, '10':21, 'J':21, 'Q':21, 'K':21, 'A':22, '2':23, '3':24, '4':25}
        singleton_ratings_map = {'5':0, '6':1, '7':2, '8':3, '9':4, '10':5, 'J':5, 'Q':5, 'K':5, 'A':6, '2':7, '3':8, '4':9}
        
        ratings_list = []
       
        # Get information about all pairs in the hand
        pair_info = PairCombination().score(hand)
        
        # Iterate through each card in the hand and determine its rating, greedily applying the rules commented above

        for c in hand:

            have_pair_of_c = False
            for pair in pair_info.instance_list:
                if c.pips == pair[0].pips:
                    # We have a pair of c's in the hand
                    have_pair_of_c = True
                    ratings_list.append((c, pair_ratings_map[c.pips]))
                    break # Don't need to look at any more pairs in pair_info
            if have_pair_of_c: continue # Greedy algorith, so done rating the card

            # If card c is an 8, do we also have a 6? {scenario (2)}
            if c.pips == '8':
                # Card c is an 8
                list_of_6s = [c6 for c6 in hand if c6.pips=='6']
                if len(list_of_6s) > 0:
                    # We also have one or more 6's in the hand
                    ratings_list.append((c, 16))
                    continue # Greedy algorith, so done rating the card

            # If card c is a 7, do we also have a 9? {scenario (3)}
            if c.pips == '7':
                # Card c is an 7
                list_of_9s = [c9 for c9 in hand if c9.pips=='9']
                if len(list_of_9s) > 0:
                    # We also have one or more 9's in the hand
                    ratings_list.append((c, 15))
                    continue # Greedy algorith, so done rating the card

            # If card c is a 10, J, Q, or K, do we also have a 5? {scenario (4)}
            if c.pips == '10' or c.pips == 'J' or c.pips == 'Q' or c.pips == 'K':
                # Card c is an 10 or Face
                list_of_5s = [c5 for c5 in hand if c5.pips=='5']
                if len(list_of_5s) > 0:
                    # We also have one or more 5's in the hand
                    ratings_list.append((c, 14))
                    continue # Greedy algorith, so done rating the card

            # If card c is a 9, do we also have a 6? {scenario (5a)}
            if c.pips == '9':
                # Card c is an 9
                list_of_6s = [c6 for c6 in hand if c6.pips=='6']
                if len(list_of_6s) > 0:
                    # We also have one or more 6's in the hand
                    ratings_list.append((c, 13))
                    continue # Greedy algorith, so done rating the card

            # If card c is an 8, do we also have a 7? {scenario (5b)}
            if c.pips == '8':
                # Card c is an 8
                list_of_7s = [c7 for c7 in hand if c7.pips=='7']
                if len(list_of_7s) > 0:
                    # We also have one or more 7's in the hand
                    ratings_list.append((c, 12))
                    continue # Greedy algorith, so done rating the card
            
            # If card c is a 7, do we also have a 8? {scenario (5c)}
            if c.pips == '7':
                # Card c is a 7
                list_of_8s = [c8 for c8 in hand if c8.pips=='8']
                if len(list_of_8s) > 0:
                    # We also have one or more 8's in the hand
                    ratings_list.append((c, 11))
                    continue # Greedy algorith, so done rating the card

            # If card c is a 6, do we also have a 9? {scenario (5d)}
            if c.pips == '6':
                # Card c is a 6
                list_of_9s = [c9 for c9 in hand if c9.pips=='9']
                if len(list_of_9s) > 0:
                    # We also have one or more 9's in the hand
                    ratings_list.append((c, 10))
                    continue # Greedy algorith, so done rating the card

            # Lastly, rate the card as a singleton {scenario (6) and (7)}
            ratings_list.append((c, singleton_ratings_map[c.pips]))
        
        return ratings_list

    def rate_follows_in_hand(self, hand = Hand(), pile = Hand()):
        """
        Utility function that provides a "score" or (later) an arbitrary "rating" for each card in the hand. The rating is chosen such that
        the card with the highest rating is the card that is considered a better follow, meaning that it is more likely to generate more play
        points for the leader and generate less play points for the opponent. Initial implementation is to play a card that will lead immediately
        to the highest play score. Possibly in the future incorporate playing on or off a potential sequence, etc.
        :parameter hand: The hand of cards for which to generate scores/ratings, Hand object
        :parameter pile: The play pile to use to test for play scores. Includes all previously played cards in the go round., Hand object
        :return: List of tuples (Card, Score/Rating), [(Card object, int)]
        """
        return_val = []

        # Highest priority is to play a card in the hand which generates play points.
        # So, iterate through the playable cards one at a time, creating a play pile with that card as the last, test that play pile for
        # play scoring combinations, or for increasing the go round count to 31, and score the card accordingly.

        for card in hand:
            # Add card to pile
            pile.add_cards(card)

            # Score the pile using play scoring combinations
            score = 0
            for combo in self._play_combinations:
                assert(isinstance(combo, CribbageCombinationPlaying))
                info = combo.score(pile)
                score += info.score
            # If card score is 0, and if card  would make the go round count 31, then score the card as 2
            if score == 0:
                if sum([c.count_card() for c in pile]) == 31:
                    score = 2
            # Use the pile score or the score for reaching 31 as the score/rating for card
            return_val.append((card, score))

            # Remove card from pile
            pile.remove_card()

        # If no card has received a non-zero score above, then provide an arbitrary "ranking" based on pips, where higher pip value
        # provides a higher ranking for the card. This should lean in the direction of both defensively pushing the go round count past
        # 15 and pushing the go round count as close to 31 as possible to try to force a declaration of GO from oponent.

        if sum([rv[1] for rv in return_val]) == 0:
            # No card received a non-zero score above, thus there are no cards that can be played for play points
            # Clear return_val and start over, since we can't modify the tuples in the list
            return_val = []
            for card in hand:
                return_val.append((card, card.count_card()))

        # TODO: Consider adding logic to value playing on (offensive) or playing off (defensive) an emerging potential run on the play pile
        
        return return_val

    # TODO: Create another member that returns expected values for a hand. Like a 0.25 points expected value for a jack in the hand.
    # or a (16/52)*2 EV for a 5 in the hand, based on a ten or face card being drawn as starter. What is the EV for a 2 card sequence?
    # What is the EV for a 2 card sequence with gap of one inbetween? Etc. If this is implemented, the concept is it is a secondary prioritization
    # for crib forming, over guaranteed points available in the hand. It might also be used to help determine what card to follow or go.


class HoyleishDealerCribbagePlayStrategy(HoyleishCribbagePlayStrategy):
    """
    Dealer play strategy based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations
    from Hoyle may be implemented, and other strategy components may be implemented alternatively or in addition too. Dealer and player require
    different form_crib(...) implementations because it's okay for the dealer to place points in the crib, whereas the player should almost
    always avoid doing so.
    """
    
    # For the Dealer, crib formation will be based on maximizing (score in hand) + (score in crib).
    def form_crib(self, xfer_to_crib_callback, get_hand_callback, play_recorder_callback=None):
        """
        Forms the crib based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations
        from Hoyle may be implemented, and other strategy components may be implemented alternatively or in addition too.
        :parameter xfer_to_crib_callback: Bound method used to transfer cards from hand to crib, e.g., CribbageDeal.xfer_player_card_to_crib
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: None
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(xfer_to_crib_callback))
        assert(callable(get_hand_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # First crib lay away strategy from Hoyle is to count up all the show points in the hand and lay away the two cards that
        # leave the maximum possible score for the four that will remain in the hand. Here this will be augmented/modified by maximizing the combined
        # score in the hand and the crib.
         
        # Get the cards in the hand
        cards = get_hand_callback()
       
        # Generate permutations of 4-card hands / 2-card crib contributions, and score them
        h = Hand().add_cards(cards)
        priority_list = self.permute_and_score_dealt_hand(h)
        
        # Sort priority_list by descending (guaranteed_hand_score + guaranteed_crib_score)
        sorted_list = sorted(priority_list, key = lambda option: (option.hand_score + option.crib_score), reverse = True)

        # TODO: Could now filter sorted_list for all options that have the same hand_score + crib_score as the first item on the sorted list,
        # and output a debug message, probably including str(sorted_list[i] for each such option), to start to build statistics on how
        # often this prioritization scheme is ambiguous. This would be evidence of potential value in further work on prioritization, such as
        # incorporating expected probability scores.

        # Now transfer to the crib the crib cards for the highest priority option
        for c in sorted_list[0].crib:
            i = cards.index(c)
            xfer_to_crib_callback(i)
            # Refresh cards, since we've pulled a card out of the hand, and thus changed the indexing
            cards = get_hand_callback()
 
        return None


class HoyleishPlayerCribbagePlayStrategy(HoyleishCribbagePlayStrategy):
    """
    Player play strategy based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations
    from Hoyle may be implemented, and other strategy components may be implemented alternatively or in addition too. Dealer and player require
    different form_crib(...) implementations because it's okay for the dealer to place points in the crib, whereas the player should almost
    always avoid doing so.
    """
    
    # For the Player, crib formation will be based on maximizing (score in hand) - (score in crib).
    def form_crib(self, xfer_to_crib_callback, get_hand_callback, play_recorder_callback=None):
        """
        Forms the crib based initially/roughly on "Strategy for Cribbage" described in Hoyle. The "ish" implies that not all recommendations
        from Hoyle may be implemented, and other strategy components may be implemented alternatively or in addition too.
        :parameter xfer_to_crib_callback: Bound method used to transfer cards from hand to crib, e.g., CribbageDeal.xfer_player_card_to_crib
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: None
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(xfer_to_crib_callback))
        assert(callable(get_hand_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # First crib lay away strategy from Hoyle is to count up all the show points in the hand and lay away the two cards that
        # leave the maximum possible score for the four that will remain in the hand. Here this will be augmented/modified by maximizing the
        # score in the hand less the score in the crib.
         
        # Get the cards in the hand
        cards = get_hand_callback()
        
        # Generate permutations of 4-card hands / 2-card crib contributions, and score them
        h = Hand().add_cards(cards)
        priority_list = self.permute_and_score_dealt_hand(h)
        
        # Sort priority_list by descending (guaranteed_hand_score + guaranteed_crib_score)
        sorted_list = sorted(priority_list, key = lambda option: (option.hand_score - option.crib_score), reverse = True)

        # TODO: Could now filter sorted_list for all options that have the same (hand_score - crib_score) as the first item on the sorted list,
        # and output a debug message, probably including str(sorted_list[i] for each such option), to start to build statistics on how
        # often this prioritization scheme is ambiguous. This would be evidence of potential value in further work on prioritization, such as
        # incorporating expected probability scores.

        # Now transfer to the crib the crib cards for the highest priority option
        for c in sorted_list[0].crib:
            i = cards.index(c)
            xfer_to_crib_callback(i)
            # Refresh cards, since we've pulled a card out of the hand, and thus changed the indexing
            cards = get_hand_callback()
 
        return None


class InteractiveCribbagePlayStrategy(CribbagePlayStrategy):
    """
    Implementation of CribbagePlayStrategy where a human player is asked to decide what to do.
    """
    def form_crib(self, xfer_to_crib_callback, get_hand_callback, play_recorder_callback=None):
        """
        Ask human player which cards from the hand to place in the crib.
        :parameter xfer_to_crib_callback: Bound method used to transfer cards from hand to crib, e.g., CribbageDeal.xfer_player_card_to_crib
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: None
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(xfer_to_crib_callback))
        assert(callable(get_hand_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # We're interactive here, so ask the user which cards from their hand they want in the crib

        # Build a query for the user to obtain a decision on first card to put in the crib
        receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
        h = Hand()
        h.add_cards(get_hand_callback())
        query_preface = f"Your hand: {str(h)}\nWhat is the first card you wish to place in the crib?"
        query_dic = {}
        position = 0
        for card in get_hand_callback():
            query_dic[str(position)] = str(card)
            position += 1
        command = UserQueryCommandMenu(receiver, query_preface, query_dic)
        response = command.Execute()
        xfer_to_crib_callback(int(response))
        if play_recorder_callback: play_recorder_callback(f"{response}\\n")
        
        # Build a query for the user to obtain a decision on second card to put in the crib
        h = Hand()
        h.add_cards(get_hand_callback())
        query_preface = f"Your hand: {str(h)}\nWhat is the second card you wish to place in the crib?"
        query_dic = {}
        position = 0
        for card in get_hand_callback():
            query_dic[str(position)] = str(card)
            position += 1
        command = UserQueryCommandMenu(receiver, query_preface, query_dic)
        response = command.Execute()
        xfer_to_crib_callback(int(response))
        if play_recorder_callback: play_recorder_callback(f"{response}\\n")

        return None

    def follow(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, play_recorder_callback=None):
        # TODO: This doc string needs arguments documented for the callback functions, as do several other doc strings in this module.
        """
        Ask human player which card to follow (play) in a go round.
        :parameter go_count: The current cumulative count of the go round before the follow, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: (The pips count of the card played as int, Go declared as boolean), tuple
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        
        # We're interactive here, so ask the user which card from their hand they want to play

        # Generate list of which if any cards can still be played, which will use "lightly" later.
        # "Lightly" meaning that we will not restrict the list of cards available to choose from, though we will validate that any
        # choice by the user is a valid play.
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - go_count)]

        declare_go = False
        valid_choice = False
        
        # Build a query for the user to obtain a decision on card to play
        receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
        query_preface = 'Current play count is ' + str(go_count) + '. What card do you wish to play?'
        query_dic = {}
        position = 0
        for card in get_hand_callback():
            query_dic[str(position)] = str(card)
            position += 1
        if len(playable) == 0:
            # User has no playable cards, so add 'Go' to the list of choices
            query_dic['g'] = 'Go'
        command = UserQueryCommandMenu(receiver, query_preface, query_dic)
        response = command.Execute()
        
        while not valid_choice:

            if response == 'g':
                valid_choice = True
                declare_go = True
                count = 0
            else:
                # Determine if the chosen card can be played without go_count exceeding 31.
                chosen_card_count = get_hand_callback()[int(response)].count_card()
                if (go_count + chosen_card_count) <= 31:
                    # Card can be played
                    count = play_card_callback(int(response))
                    valid_choice = True
                else:
                    # Card cannot be played
                    # Inform the user and ask for another card choice
                    query_preface = 'Chosen card would cause cumulative play count to exceed 31. What card do you wish to play?'
                    query_dic = {}
                    position = 0
                    for card in get_hand_callback():
                        query_dic[str(position)] = str(card)
                        position += 1
                    if len(playable) == 0:
                        # User has no playable cards, so add 'Go' to the list of choices
                        query_dic['g'] = 'Go'
                    command = UserQueryCommandMenu(receiver, query_preface, query_dic)
                    response = command.Execute()
                    
        if play_recorder_callback: play_recorder_callback(f"{response}\\n")
        
        return (count, declare_go)

    def go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback,
           play_recorder_callback=None):
        """
        Ask human player which card(s) if any to play in a go round after their opponent has declared go.
        :parameter go_count: The current cumulative count of the go round that caused opponent to declare go, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter score_play_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.determine_score_playing
        :parameter peg_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.peg_for_player
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: The sum of pips count of any cards played, int
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(score_play_callback))
        assert(callable(peg_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        
        play_count = go_count
        
        # Generate list of which if any cards can still be played
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]

        while (len(playable) > 0):
        
            # We're interactive here, so ask the user which card from playable they want to play

            # Build a query for the user to obtain a decision on card to play
            receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
            query_preface = 'Opponent has declared GO. Current play count is ' + str(play_count) + '. What card do you wish to play?'
            query_dic = {}
            position = 0
            for card in playable:
                query_dic[str(position)] = str(card)
                position += 1
            command = UserQueryCommandMenu(receiver, query_preface, query_dic)
            response = command.Execute()
            if play_recorder_callback: play_recorder_callback(f"{response}\\n")

            # Play card
            card = playable[int(response)]
            play_card_callback(get_hand_callback().index(card))
            play_count += card.count_card()

            # Score any pairs or runs due to the played card
            reasons = []
            score_count = score_play_callback(get_play_pile_callback(), score_reasons=reasons)
            try:
                peg_callback(score_count, reasons)
            except CribbageGameOverError as e:
                # (except covered by unit test)
                # Raise a new CribbageGameOverError with the added information about score during play
                raise CribbageGameOverError(e.args, go_play_score = score_count)

            # Generate list of which if any cards can still be played
            playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]
        
        return (play_count - go_count)

    def continue_save_end(self):
        """
        Ask human player if game play should continue by proceeding to the next deal, if current game state should be saved and game play ended,
        or if game play should be ended without saving current game state.
        :return: Tuple (Continue Game True/False, Save Game State True/False). If first tuple value is True, second tuple value should be ignored.
        """
        receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
        query_preface = f"Do you wish to keep playing?"
        query_dic = {'c':'Continue game', 's':'Save and end game', 'e':'End game'}
        command = UserQueryCommandMenu(receiver, query_preface, query_dic)
        response = command.Execute()
        
        keep_playing = False
        save_state = False
        
        match response:
            case 'c':
                keep_playing = True
            case 's':
                save_state = True
            case 'e':
                pass
        
        return (keep_playing, save_state)


class RandomCribbagePlayStrategy(CribbagePlayStrategy):
    """
    CribbagePlayStrategy that simply chooses randomly from hand to form crib, and randomly from playable cards to follow or go.
    This of course is a very unintelligent automatic play strategy, but as such, it is intended to be a reference against which to compare
    other automatic play strategies.
    """
    def __init__(self):
        """
        Construct an object of this class.
        """
        # Instantiate a random number generator to be used for selecting cards by this strategy.
        # This is intended to keep this randmom number stream isolated from the random number stream that draws cards, so that
        # comparison of playing a game with two different strategies has both the games see the same card draws, provided a seed for
        # the drawing random number generator is provided.
        self._random_generator = random.Random()
        # All elements of the _guaranteed_4card_combinations and _guaranteed_2card_combinations lists must be children of
        # CribbageCombinationShowing class.
        self._guaranteed_4card_combinations = [PairCombination(), FifteenCombination(), RunCombination(), FlushCombination()]
        self._guaranteed_2card_combinations = [PairCombination(), FifteenCombination()]
        # All elements of the _play_combinations list must be children of CribbageCombinationPlaying class.
        self._play_combinations = [FifteenCombinationPlaying(), PairCombinationPlaying(), RunCombinationPlaying()]
 
    def follow(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, play_recorder_callback=None):
        """
        Follows (plays) a random playable card.
        :parameter go_count: The current cumulative count of the go round before the follow, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: (The pips count of the card played as int, Go declared as boolean), tuple
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))
        
        # Default tuple to return, arbitrarily here a GO tuple, but expected to be set in all branches below
        return_val = (0, True)
        
        # Determine list of cards in the hand that can be played without go_count exceeding 31.
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - go_count)]

        if len(playable) > 0:
            if len(get_play_pile_callback()) == 0:
                # The play pile has no cards in it, so this is a lead, so call lead(...) method
                h = Hand()
                h.add_cards(playable)
                (count, card) = self.lead(h)
                play_card_callback(get_hand_callback().index(card))
                return_val = (count, False)
            else:
                # Apply logic for following - which is just to pick a random card from playable list
                card = playable[self._random_generator.randrange(len(playable))]
                count = card.count_card()
                play_card_callback(get_hand_callback().index(card))
                return_val = (count, False)
                
        else:
            # If no cards in the hand can be played, then return (0, True), in other words, declare GO.
            return (0, True) 

        return return_val

    def go(self, go_count, play_card_callback, get_hand_callback, get_play_pile_callback, score_play_callback, peg_callback,
           play_recorder_callback=None):
        """
        Randomly selects which card(s) if any to play in a go round after opponent has declared go.
        :parameter go_count: The current cumulative count of the go round that caused opponent to declare go, int
        :parameter play_card_callback: Bound method used to play a card from hand, e.g., CribbageDeal.play_card_for_player
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter get_play_pile_callback: Bound method used to obtain the pile of played cards, e.g., CribbageDeal.get_player_hand
        :parameter score_play_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.determine_score_playing
        :parameter peg_callback: Bound method used to determine any scoring while go is being played out, e.g., CribbageDeal.peg_for_player
        :parameter play_recorder_callback: Bound method used to record user choices for cards to play during the go
        :return: The sum of pips count of any cards played, int
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(play_card_callback))
        assert(callable(get_hand_callback))
        assert(callable(get_play_pile_callback))
        assert(callable(score_play_callback))
        assert(callable(peg_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # The overall process flow in this function is the same as for 

        play_count = go_count
        
        # Generate list of which if any cards can still be played
        playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]

        while (len(playable) > 0):

            # Randomly select a card to play from the playable list
            card = playable[self._random_generator.randrange(len(playable))]
            count = card.count_card()

            # Play card
            play_card_callback(get_hand_callback().index(card))
            play_count += count

            # Score any pairs or runs due to the played card
            reasons = []
            score_count = score_play_callback(get_play_pile_callback(), score_reasons=reasons)
            try:
                peg_callback(score_count, reasons)
            except CribbageGameOverError as e:
                # TODO: Cover by a unit test
                # Raise a new CribbageGameOverError with the added information about score during play
                raise CribbageGameOverError(e.args, go_play_score = score_count)

            # Generate list of which if any cards can still be played
            playable = [c for c in get_hand_callback() if c.count_card() <= (31 - play_count)]
        
        return (play_count - go_count)

    def lead(self, hand = Hand()):
        """
        Leads (plays) a first card in a go round by selecting a random playable card from the hand.
        This is a utility method intended to be called by follow(...) method, not by outsiders.
        :parameter hand: The hand from which to lead a card, Hand object
        :return: Tuple of (The pips count of the card to be led, The card to be led) (int, Card object) 
        """

        # Get a random card out of the hand
        lead_card = hand[self._random_generator.randrange(len(hand))]
        lead_count = lead_card.count_card()
        
        return (lead_count, lead_card)

    def form_crib(self, xfer_to_crib_callback, get_hand_callback, play_recorder_callback=None):
        """
        Forms the crib based on randomly selecting cards from the hand.
        :parameter xfer_to_crib_callback: Bound method used to transfer cards from hand to crib, e.g., CribbageDeal.xfer_player_card_to_crib
        :parameter get_hand_callback: Bound method used to obtain cards in hand, e.g., CribbageDeal.get_player_hand
        :parameter play_recorder_callback: Bound method used to record user choices for cards to lay off in the crib
        :return: None
        """
        # Sanity check the arguments to make sure they are callable. This does not guarantee they are bound methods, e.g., a class is callable
        # for construction. But it is better than nothing.
        assert(callable(xfer_to_crib_callback))
        assert(callable(get_hand_callback))
        if play_recorder_callback: assert(callable(play_recorder_callback))

        # Get the cards in the hand
        cards = get_hand_callback()

        # Transfer the first card to the crib by selecting randomly from cards
        crib_card_1 =cards[self._random_generator.randrange(len(cards))]
        xfer_to_crib_callback(cards.index(crib_card_1))

        # Refresh the list of cards to select from since we've transferred one out to the crib
        cards = get_hand_callback()

        # Transfer the second card to the crib by selecting randomly from cards
        crib_card_2 =cards[self._random_generator.randrange(len(cards))]
        xfer_to_crib_callback(cards.index(crib_card_2))
 
        return None

    def continue_save_end(self):
        """
        Determine if game play should continue by proceeding to the next deal, if current game state should be saved and game play ended,
        or if game play should be ended without saving current game state. Since this strategy is for automatic play (i.e., for a machine player),
        answer will always be to continue the game.
        :return: Tuple (Continue Game True/False, Save Game State True/False). If first tuple value is True, second tuple value should be ignored.
        """
        return (True, False)
