"""
Defines classes used to represent and play through a single deal of a game of cribbage.

Exported Classes:
    CribbagePlayers - Enumeration of the participants in a cribbage game.
    CribbageRole - Enumeration of the roles of players in a cribbage deal. On alternating deals the enumerated
                    CribbagePlayers will alternate CribbageRole's.
    CribbageDealInfo -  Used to return information about the results of a cribbage deal, from CribbageDeal.play(...).
    CribbageDeal - Represents a single deal in cribbage, to be played out by a dealer and a player.

Exported Exceptions:
    None    
 
Exported Functions:
    None

Logging:
    Uses a logger named 'cribbage_logger' for providing game output to the user. This logger is configured
    by calling CribbageSimulator.setup_logging(...).
 """

# Standard imports
import logging
from enum import Enum

# Local imports
from CribbageSim.CribbageGameOutputEvents import CribbageDealPhase
from HandsDecksCards.card import Card
from HandsDecksCards.deck import Deck, StackedDeck
from HandsDecksCards.hand import Hand
from CribbageSim.CribbagePlayStrategy import CribbagePlayStrategy
from CribbageSim.CribbageCombination import CribbageCombinationShowing, CribbageComboInfo, PairCombination, FifteenCombination, RunCombination, FlushCombination, HisNobsCombination
from CribbageSim.CribbageCombination import CribFlushCombination
from CribbageSim.CribbageCombination import CribbageCombinationPlaying, FifteenCombinationPlaying, PairCombinationPlaying, RunCombinationPlaying
from CribbageSim.exceptions import CribbageGameOverError
from CribbageSim.CribbageGameOutputEvents import CribbageGameOutputEvents, CribbageGameLogInfo


class CribbagePlayers(Enum):
    """
    An enumeration of the participants in a cribbage game.
    """
    PLAYER_1 = 1 
    PLAYER_2 = 2


class CribbageRole(Enum):
    """
    An enumeration of the roles of participants in a cribbage game.
    """
    DEALER = 1 
    PLAYER = 2


# TODO: Consider using @dataclass decoration from module dataclasses for this type of member only class throughout.
# See (https://docs.python.org/3/library/dataclasses.html#module-dataclasses)
class CribbageDealInfo:
    """
    A class with all members/attributes considered public. Used to return information about the results of a cribbage deal,
    from CribbageDeal.play(...).
    """
    def __init__(self):
        """
        Create and initialize attributes.
        """
        self.player_play_score = 0
        self.player_show_score = 0
        self.dealer_play_score = 0
        self.dealer_his_heals_score = 0 # Starter card was a J
        self.dealer_show_score = 0
        self.dealer_crib_score = 0


class CribbageDeal:
    """
    Class representing a single deal in cribbage, to be played out by a dealer and a player.
    """
    
    def __init__(self, player_strategy = CribbagePlayStrategy(), dealer_strategy = CribbagePlayStrategy(),
                 player_peg_callback = None, dealer_peg_callback = None, player_participant = None, dealer_participant = None):
        """
        Construct a finite deck of Cards, an empty dealer Hand, an empty player Hand, and, and empty crib Hand.
        Create a starter card, which is expected to be replaced with a dealt one.
        Set strategies for dealer and player hand play.
        Create empgy Hand(s) for the dealer and player "played cards" piles during a go round. Also create an empty Hand for the combined
            pile. Expect combined pile to be passed as information to play strategies when following, and for scoring determination
            during play. Expect individual piles to be displayed such as during interactive play.
        :parameter player_strategy: CribbagePlayStrategy instance used to play player hand, CribbagePlayStrategy or child instance
        :parameter dealerer_strategy: CribbagePlayStrategy instance used to play dealer hand, CribbagePlayStrategy or child instance
        :parameter player_peg_callback: Bound method for communicating scoring for player back to a game, e.g. CribbageGame.peg_for_player1
        :parameter dealer_peg_callback: Bound method for communicating scoring for dealer back to a game, e.g. CribbageGame.peg_for_player2
        :parameter player_participant: Which game participant is the player for this deal?, CribbagePlayers Enum
        :parameter dealer_participant: Which game participant is the dealer for this deal?, CribbagePlayers Enum
        """
        self._deck = Deck(isInfinite = False) # So that self has a valid _deck attribute when self.reset_deal() is called
        self.reset_deal(player_peg_callback,dealer_peg_callback,player_participant,dealer_participant)
        self.set_dealer_play_strategy(dealer_strategy)
        self.set_player_play_strategy(player_strategy)
        # All elements of the _play_combinations list must be children of CribbageCombinationPlaying class.
        self._play_combinations = [FifteenCombinationPlaying(), PairCombinationPlaying(), RunCombinationPlaying()]
        # All elements of the _hand_show_combinations list must be children of CribbageCombinationShowing class.
        self._hand_show_combinations = [PairCombination(), FifteenCombination(), RunCombination(), FlushCombination(), HisNobsCombination()]
        # All elements of the  list must be children of CribbageCombinationShowing class.
        self._crib_show_combinations = [PairCombination(), FifteenCombination(), RunCombination(), CribFlushCombination(), HisNobsCombination()]

    def reset_deal(self, player_peg_callback = None, dealer_peg_callback = None, player_participant = None, dealer_participant = None):
        """
        Reset everything as necessary to have a fresh deal.
        :parameter player_peg_callback: Bound method for communicating scoring for player back to a game, e.g. CribbageDeal.peg_for_player1
        :parameter dealer_peg_callback: Bound method for communicating scoring for dealer back to a game, e.g. CribbageDeal.peg_for_player2
        :parameter player_participant: Which game participant is the player for this deal?, CribbagePlayers Enum
        :parameter dealer_participant: Which game participant is the dealer for this deal?, CribbagePlayers Enum
        :return: None
        """
        # If a StackDeck has been injected, for example as part of unit testing, then leave it in place
        if not isinstance(self._deck, StackedDeck): self._deck = Deck(isInfinite = False)
        self._dealer_hand = Hand()
        self._dealer_pile = Hand()
        self._dealer_score = 0
        self._player_hand = Hand()
        self._crib_hand = Hand()
        self._player_pile = Hand()
        self._player_score = 0
        self._combined_pile = Hand()
        self._starter = Card()
        # A string that could be used to help build a unit test, by passing it to @patch('sys.stdin', io.StringIO(_recorded_play)
        self._recorded_play = ''
        if (player_peg_callback): assert(callable(player_peg_callback))
        if (dealer_peg_callback): assert(callable(dealer_peg_callback))
        self._player_peg_callback = player_peg_callback
        self._dealer_peg_callback = dealer_peg_callback
        self._participant_player = player_participant
        self._participant_dealer = dealer_participant
        return None
        
    def last_card_played(self, combined_pile = None):
        """
        Return the most recent played card, that is, the last card in the list self._combined_pile.
        :parameter combined_pile: If not None, then score this pile, otherwise score self._combined_pile. If not None, must be a Hand() object.
        :return: The most recent played card, Card object
        """
        if combined_pile:
            assert(len(combined_pile)>0)
            return combined_pile[len(combined_pile)-1]
        else:
            assert(len(self._combined_pile)>0)
            return self._combined_pile[len(self._combined_pile)-1]
        
    def record_play(self, play_string = ''):
        """
        A utility function intended to help with creating unit tests. play_string argument is appended to self._recorded_play. The concept is that
        if self._recorded_play were printed at the end of a deal, then it could be copy-pasted in as the argument to io.String in the
        @patch('sys.stdin', io.StringIO(...) decorator of a unit test that would duplicate interactive play of the deal.
        :parameter play_string: Append this string to self._recorded_play(), string
        :return: None
        """
        self._recorded_play += play_string
        return None
        
    def set_player_play_strategy(self, ps = CribbagePlayStrategy()):
        """
        Set the player play strategy.
        :parameter ps: The player play strategy, CribbagePlayStrategy()
        :return: None
        """
        assert(isinstance(ps, CribbagePlayStrategy))
        self._player_play_strategy = ps
        return None
            
    def set_dealer_play_strategy(self, ps = CribbagePlayStrategy()):
        """
        Set the dealer play strategy.
        :parameter ps: The dealer play strategy, CribbagePlayerPlayStrategy()
        :return: None
        """
        assert(isinstance(ps, CribbagePlayStrategy))
        self._dealer_play_strategy = ps
        return None

    def get_combined_play_pile(self):
        """
        Return a list of cards in the combined play pile.
        :return: A list of the cards in the combined play pile, List of Card instances
        """
        return list(self._combined_pile.get_cards())
    
    def draw_for_dealer(self, number=1):
        """
        Draw one or more cards from deck into dealer's hand.
        :parameter number: How many cards to draw into dealer's hand, int
        :return: A list of Card(s) in the hand after the draw
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card_list = self._dealer_hand.add_cards(self._deck.draw(number))

        # If dealer for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_dealer == CribbagePlayers.PLAYER_1:
            logger.info(f"Hand for {self._participant_dealer} after dealing: {self._dealer_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._dealer_hand)))
        elif self._participant_dealer == CribbagePlayers.PLAYER_2:
            logger.debug(f"Hand for {self._participant_dealer} after dealing: {self._dealer_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._dealer_hand)))

        return card_list

    def draw_for_player(self, number=1):
        """
        Draw one or more cards from deck into player's hand.
        :parameter number: How many cards to draw into player's hand, int
        :return: A list of Card(s) in the hand after the draw
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card_list = self._player_hand.add_cards(self._deck.draw(number))

        # If player for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_player == CribbagePlayers.PLAYER_1:
            logger.info(f"Hand for {self._participant_player} after deal: {self._player_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._player_hand)))
        elif self._participant_player == CribbagePlayers.PLAYER_2:
            logger.debug(f"Hand for {self._participant_player} after deal: {self._player_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._player_hand)))

        return card_list

    def get_player_hand(self):
        """
        Return the cards remaining in the player's hand as a list.
        :return: List of cards that are remaining in the player's hand, list
        """
        return list(self._player_hand.get_cards())

    def get_dealer_hand(self):
        """
        Return the cards remaining in the dealer's hand as a list.
        :return: List of cards that are remaining in the dealer's hand, list
        """
        return list(self._dealer_hand.get_cards())

    def draw_starter_card(self):
        """
        Draw one card from deck to be the starter card.
        :return: The starter card, Card object
        """
        self._starter = self._deck.draw()
        return self._starter

    def play_card_for_player(self, index = 0):
        """
        Play the card at index location in the player's hand. Remove it from the player's hand, and add it to the player's and combined piles.
        :parameter index: The index location in the player's hand of the card to play, int [0...number of cards in hand - 1]
        :return: The pips count of the card played, int
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card = self._player_hand.remove_card(index)
        self._player_pile.add_cards(card)
        self._combined_pile.add_cards(card)
        
        # Compute the total count of the play pile.
        go_round_count = self._combined_pile.count_hand()

        # If player for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_player == CribbagePlayers.PLAYER_1:
            logger.info(f"     Hand for player {self._participant_player} after playing {card}: {self._player_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._player_hand)))
            # Also log to info update player1 play pile
            logger.info(f"     Pile for player {self._participant_player} after playing {card}: {self._player_pile}",
                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_PILE, pile_player1=str(self._player_pile)))
        elif self._participant_player == CribbagePlayers.PLAYER_2:
            logger.debug(f"     Hand for player {self._participant_player} after playing {card}: {self._player_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._player_hand)))
            # Also log to info update player2 play pile
            logger.info(f"     Pile for player {self._participant_player} after playing {card}: {self._player_pile}",
                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_PILE, pile_player2=str(self._player_pile)))

        # Log updated combined play pile to info
        logger.info(f"Combined pile after player {self._participant_player} played {card}: {self._combined_pile}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PILE_COMBINED, pile_combined=str(self._combined_pile),
                                              go_round_count=go_round_count))

        return card.count_card()
        
    def play_card_for_dealer(self, index = 0):
        """
        Play the card at index location in the dealer's hand. Remove it from the dealer's hand, and add it to the dealer's and combined piles.
        :parameter index: The index location in the dealer's hand of the card to play, int [0...number of cards in hand - 1]
        :return: The pips count of the card played, int
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card = self._dealer_hand.remove_card(index)
        self._dealer_pile.add_cards(card)
        self._combined_pile.add_cards(card)

        # Compute the total count of the play pile.
        go_round_count = self._combined_pile.count_hand()

        # If dealer for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_dealer == CribbagePlayers.PLAYER_1:
            logger.info(f"     Hand for dealer {self._participant_dealer} after playing {card}: {self._dealer_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._dealer_hand)))
            # Also log to info update player1 play pile
            logger.info(f"     Pile for dealer {self._participant_dealer} after playing {card}: {self._dealer_pile}",
                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_PILE, pile_player1=str(self._dealer_pile)))
        elif self._participant_dealer == CribbagePlayers.PLAYER_2:
            logger.debug(f"     Hand for dealer {self._participant_dealer} after playing {card}: {self._dealer_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._dealer_hand)))
            # Also log to info update player2 play pile
            logger.info(f"     Pile for dealer {self._participant_dealer} after playing {card}: {self._dealer_pile}",
                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_PILE, pile_player2=str(self._dealer_pile)))

        # Log updated combined play pile to info
        logger.info(f"Combined pile after dealer {self._participant_dealer} played {card}: {self._combined_pile}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PILE_COMBINED, pile_combined=str(self._combined_pile),
                                              go_round_count=go_round_count))

        return card.count_card()

    # TODO: Identify a solution such that this method is not duplicated in the deal, game, and board classes.
    def _make_reasons_string(self, reasons=[]):
        """
        Utility , that converts a list of CribbageComboInfo objects to a string.
        :parameter reasons: List of CribbageComboInfo objects
        :returnb reasons_string: A string representing the list of reasons
        """
        reasons_string=''
        for reason in reasons:
            reasons_string += f"{str(reason)}\n"
        return reasons_string

    def peg_for_player(self, count = 1, reasons = [], during = CribbageDealPhase.NO_PHASE):
        """
        Add count to the player's score.
        :parameter count: The number of pegs (points) to add to the player's score, int
        :parameter reasons: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: The current player point score, int
        """
        if count > 0:
            # Update score for the deal
            self._player_score += count
            # Update score for the game
            if (self._player_peg_callback):
                self._player_peg_callback(count, reasons, during)
            else:
                # No callback available to peg for player, so, log scoring info from here
                # Get the logger 'cribbage_logger'
                logger = logging.getLogger('cribbage_logger')
                logger.info(f"Player pegs a total of {count} for:\n{self._make_reasons_string(reasons)}")
        return self._player_score

    def peg_for_dealer(self, count = 1, reasons = [], during = CribbageDealPhase.NO_PHASE):
        """
        Add count to the dealer's score.
        :parameter count: The number of pegs (points) to add to the dealer's score, int
        :parameter reasons: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: The current dealer point score, int
        """
        if count > 0:
            # Update score for the deal
            self._dealer_score += count
            # Update score for the game
            if (self._dealer_peg_callback):
                self._dealer_peg_callback(count, reasons, during)
            else:
                # No callback available to peg for dealer, so, log scoring info from here
                # Get the logger 'cribbage_logger'
                logger = logging.getLogger('cribbage_logger')
                logger.info(f"Dealer pegs a total of {count} for:\n{self._make_reasons_string(reasons)}")                
        return self._dealer_score

    def xfer_player_card_to_crib(self, index = 0):
        """
        Transfer the card at index location in the player's hand to the crib. Remove it from the player's hand.
        NOTE: Be very careful about calling this twice in a row without calling get_player_hand(...) and determining the index you want to transfer
        from that returned list of Cards, since removing Cards from Hand will change indexing if not moving exclusively from higher to lower indices.
        :parameter index: The index location in the player's hand of the card to play, int [0...number of cards in hand - 1]
        :return None:
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card = self._player_hand.remove_card(index)
        self._crib_hand.add_cards(card)

        # If player for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_player == CribbagePlayers.PLAYER_1:
            logger.info(f"     Hand for {self._participant_player} after laying {card} in crib: {self._player_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._player_hand)))
        elif self._participant_player == CribbagePlayers.PLAYER_2:
            logger.debug(f"     Hand for {self._participant_player} after laying {card} in crib: {self._player_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._player_hand)))

        return None

    def xfer_dealer_card_to_crib(self, index = 0):
        """
        Transfer the card at index location in the dealer's hand to the crib. Remove it from the dealer's hand.
        NOTE: Be very careful about calling this twice in a row without calling get_dealer_hand(...) and determing the index you want to transfer
        from that returned list of Cards, since removing Cards from Hand will change indexing if not moving exclusively from higher to lower indices.
        :parameter index: The index location in the dealer's hand of the card to play, int [0...number of cards in hand - 1]
        :return None:
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        card = self._dealer_hand.remove_card(index)
        self._crib_hand.add_cards(card)

        # If dealer for this deal is player1 for the game, then we can log an updated hand to INFO, otherwise log it to DEBUG
        if self._participant_dealer == CribbagePlayers.PLAYER_1:
            logger.info(f"     Hand for {self._participant_dealer} after laying {card} in crib: {self._dealer_hand}",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER1_HAND, hand_player1=str(self._dealer_hand)))
        elif self._participant_dealer == CribbagePlayers.PLAYER_2:
            logger.debug(f"     Hand for {self._participant_dealer} after laying {card} in crib: {self._dealer_hand}",
                         extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_PLAYER2_HAND, hand_player2=str(self._dealer_hand)))

        return None

    def determine_score_showing_hand(self, hand = Hand(), starter = None, score_reasons = []):
        """
        Determine the score of hand during show.
        :parameter hand: The hand to score, Hand instance
        :parameter starter: The starter card, Card instance
        :parameter score_info: List of CribbageComboInfo objects associated with the returned score. An empty list is expected to be passed in
            as an argument, and it will be populated by this method. Since a list is mutable, the outside one passed in can be modified inside
            the method.
        :return: The total score of all combinations in the hand, int
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        score = 0
        for combo in self._hand_show_combinations:
            assert(isinstance(combo, CribbageCombinationShowing))
            info = combo.score(hand, starter)
            if info.number_instances > 0:
                score_reasons.append(info)
                # TODO: Remove the following logger line, once this has been "centralized" into pegging methods.
                # logger.info(f"     {str(info)}")
            score += info.score
        return score

    def determine_score_showing_crib(self, hand = Hand(), starter = None, score_reasons = []):
        """
        Determine the score of crib during show.
        :parameter hand: The crib to score, Hand instance
        :parameter starter: The starter card, Card instance
        :parameter score_info: List of CribbageComboInfo objects associated with the returned score. An empty list is expected to be passed in
            as an argument, and it will be populated by this method. Since a list is mutable, the outside one passed in can be modified inside
            the method.
        :return: The total score of all combinations in the crib, int
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        score = 0
        for combo in self._crib_show_combinations:
            assert(isinstance(combo, CribbageCombinationShowing))
            info = combo.score(hand, starter)
            if info.number_instances > 0:
                score_reasons.append(info)
                # TODO: Remove the following logger line, once this has been "centralized" into pegging methods.
                # logger.info(f"     {str(info)}")
            score += info.score
        return score

    def determine_score_playing(self, combined_pile = Hand(), role_that_played = None, score_reasons = []):
        """
        Determine the score during play.
        :parameter hand: The combined, ordered pile of played cards to check for a score, Hand instance
        :parameter role_that_played: Which CribbageRole played the card that we are scoring?, as CribbageRole Enum
        :parameter score_reasons: List of CribbageComboInfo objects associated with the returned score. An empty list is expected to be passed in
            as an argument, and it will be populated by this method. Since a list is mutable, the outside one passed in can be modified inside
            the method.
        :return: Points scored based on play of last card, int
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        info_list = []

        score = 0
        for combo in self._play_combinations:
            assert(isinstance(combo, CribbageCombinationPlaying))
            info = combo.score(combined_pile)
            if info.number_instances > 0:
                info_list.append(info)
                score_reasons.append(info)
            score += info.score

        if score >0:
            logger.info(f"Scoring combinations from {str(role_that_played)} play of card {str(self.last_card_played(combined_pile))}:")
            for info in info_list:
                # TODO: Remove the following logger line, once this has been "centralized" into pegging methods.
                # logger.info(f"     {str(info)}")
                pass
            logger.info(f"     Score: {score}")

        return score

    def log_pegging_info(self):
        """
        Logs current state of pegging for dealer and player cumulatively during the hand.
        :return: None
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        logger.debug(f"Dealer total score thus far for the dealt hand: {self._dealer_score}")
        logger.debug(f"Player total score thus far for the dealt hand: {self._player_score}")
        return None
    
    def log_play_info(self, preface = '', go_round_count = 0):
        """
        Logs current state of hands, play piles, play count, and scores.
        :parameter preface: A string to use as a header for the output, for example to indicate that it is 'after lead', 'after follow', 'after go', etc., string
        :parameter go_round_count: The current play count during the go round, int
        :return: None
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        logger.debug(f"{preface}:")
        logger.debug(f"     Dealer hand after card played: {self._dealer_hand}") # Always debug
        logger.debug(f"     Dealer pile after card played: {self._dealer_pile}")
        logger.debug(f"     Player hand after card played: {self._player_hand}") # Always debug
        logger.debug(f"     Player pile after card played: {self._player_pile}")
        logger.debug(f"     Combined pile after played: {self._combined_pile}")
        logger.debug(f"     Play count after card played: {go_round_count}")
        return None

    # TODO: play() is very long. It would be good to refactor and break it apart into some smaller units.
    def play(self):
        """
        Play the cribbage deal.
        :return: Information about the results of the deal, CribbageDealInfo object
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        # Initialize the return object
        deal_info = CribbageDealInfo()

        # Shuffle, that is, rebuild the deck
        self._deck.create_deck()
        
        # Deal player and dealer hands from the deck. In a normal game, this would be one card at a time alternating.
        # However, in this case it is advantageous to deal all six cards to each hand at once, to facilitate using a stacked deck for testing.
        self.draw_for_player(6)
        logger.debug(f"Dealt player hand: {self._player_hand}")
        # To facilitate creating a unit test from the deal
        logger.debug(f"Dealt player hand: {repr(self._player_hand)}")
        self.draw_for_dealer(6)
        logger.debug(f"Dealt dealer hand: {self._dealer_hand}")
        # To facilitate creating a unit test from the deal
        logger.debug(f"Dealt dealer hand: {repr(self._dealer_hand)}")
        
        # Apply the player and dealer strategies to have player and dealer select two cards each from their hands to form the crib.
        self._player_play_strategy.form_crib(self.xfer_player_card_to_crib, self.get_player_hand, self.record_play)
        self._dealer_play_strategy.form_crib(self.xfer_dealer_card_to_crib, self.get_dealer_hand, self.record_play)
        logger.debug(f"Player hand after crib formed: {self._player_hand}")
        logger.debug(f"Dealer hand after crib formed: {self._dealer_hand}")
        logger.debug(f"Crib hand: {self._crib_hand}")

        # Deal the starter card. IFF it is a Jack, peg 2 for the dealer.
        starter = self.draw_starter_card()
        logger.info(f"Starter card: {starter}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_STARTER, starter=str(starter)))
        # To facilitate creating a unit test from the deal
        logger.debug(f"Starter card: {repr(starter)}")
        if starter.pips == 'J':
            # Peg 2 for dealer
            logger.info('Dealer scores 2 because the starter is a Jack, a.k.a. His Heels.')
            deal_info.dealer_his_heals_score += 2
            # Build a CribbageComboInfo object to explain the reason for scoring
            reason = CribbageComboInfo()
            reason.combo_name='His Heels'
            reason.number_instances=1
            reason.score=2
            reason.instance_list=[[starter]]
            try:
                self.peg_for_dealer(2, [reason], during = CribbageDealPhase.PLAYING_DEAL)
            except CribbageGameOverError as e:
                # (except covered by unit test)
                # Output the play record to facilitate unit test creation
                logger.debug(f"Play record: {self._recorded_play}")
                # Raise a new CribbageGameOverError with the added deal_info
                raise CribbageGameOverError('Game ended on drawing His Heels as starter', deal_info = deal_info)

        # Set variable that tracks which player will play next.
        # For the first go round of the deal, the player always leads.    
        next_to_play = CribbageRole.PLAYER    
            
        # Loop at this level to play multiple go rounds until the dealt cards for both players are exhausted 
        while len(self._dealer_hand) > 0 or len(self._player_hand) > 0:   
            
            # Set the go round cumulative score to 0
            go_round_count = 0
            go_declared = False
        
            # Clear the combined pile of cards played during the go round, as this pile is used for scoring during play
            self._combined_pile = Hand()

            # If go_declared, then it is a signal that the go round has finished inside this while loop by playing out a go, and it is
            # time to return to the outside while and launch the next go round. if go_round_count == 31, then it is a signal that the 
            # go round has finished inside this while loop by play count reaching exactly 31, and again, it is time to return to the outside
            # while loop.
            while not go_declared and go_round_count != 31:

                # Whoever is next to play follows using their play strategy.
                prefix  = 'After play by ' + str(next_to_play)
                match next_to_play:
                    case CribbageRole.PLAYER:
                        (count, go_declared) = self._player_play_strategy.follow(go_round_count, self.play_card_for_player,
                                                                                 self.get_player_hand, self.get_combined_play_pile,
                                                                                 self.record_play)
                        # Assess if any score in play has occured based on the player's follow. If so, peg it for the player.
                        if not go_declared:
                            reasons = []
                            score = self.determine_score_playing(self._combined_pile, next_to_play, reasons)
                            deal_info.player_play_score += score
                            try:
                                self.peg_for_player(score, reasons, during=CribbageDealPhase.PLAYING_DEAL)
                            except CribbageGameOverError as e:
                                # (except covered by unit test)
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                raise CribbageGameOverError('Game ended while scoring player play combination', deal_info = deal_info)
                        # Rotate who will play next
                        next_to_play = CribbageRole.DEALER
                    case CribbageRole.DEALER:
                        (count, go_declared) = self._dealer_play_strategy.follow(go_round_count, self.play_card_for_dealer,
                                                                                 self.get_dealer_hand, self.get_combined_play_pile,
                                                                                 self.record_play)
                        # Assess if any score in play has occured based on the dealer's follow. If so, peg it for the dealer.
                        if not go_declared:
                            reasons = []
                            score = self.determine_score_playing(self._combined_pile, next_to_play, reasons)
                            deal_info.dealer_play_score += score
                            try:
                                self.peg_for_dealer(score, reasons, during=CribbageDealPhase.PLAYING_DEAL)
                            except CribbageGameOverError as e:
                                # (except covered by unit test)
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                raise CribbageGameOverError('Game ended while scoring dealer play combination', deal_info = deal_info)
                        # Rotate who will play next
                        next_to_play = CribbageRole.PLAYER
                go_round_count += count
                
                self.log_play_info(prefix, go_round_count)
                if go_declared: logger.info(f"     Go Declared?: {go_declared}")
                self.log_pegging_info()
                
                # Has count for the go round reached exactly 31?
                if go_round_count == 31:
                    match next_to_play:
                        case CribbageRole.PLAYER:
                            # Since we rotate who will play next above, this means that dealer played to reach 31
                            logger.info('Go round ends with count of 31 by Dealer.')
                            deal_info.dealer_play_score += 2
                            # Build a CribbageComboInfo object to explain the reason for scoring
                            reason = CribbageComboInfo()
                            reason.combo_name='Go 31'
                            reason.number_instances=1
                            reason.score=2
                            reason.instance_list=[self._combined_pile.get_cards()]
                            try:
                                self.peg_for_dealer(2, [reason], during=CribbageDealPhase.PLAYING_DEAL)
                            except CribbageGameOverError as e:
                                # (except covered by unit test)
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                raise CribbageGameOverError('Game ended when dealer played to 31', deal_info = deal_info)
                        case CribbageRole.DEALER:
                            # Since we rotate who will play next above, this means that player played to reach 31
                            logger.info('Go round ends with count of 31 by Player.')
                            deal_info.player_play_score += 2
                            # Build a CribbageComboInfo object to explain the reason for scoring
                            reason = CribbageComboInfo()
                            reason.combo_name='Go 31'
                            reason.number_instances=1
                            reason.score=2
                            reason.instance_list=[self._combined_pile.get_cards()]
                            try:
                                self.peg_for_player(2, [reason], during=CribbageDealPhase.PLAYING_DEAL)
                            except CribbageGameOverError as e:
                                # (except covered by unit test)
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                raise CribbageGameOverError('Game ended when player played to 31', deal_info = deal_info)
                    self.log_pegging_info()
                    continue # Get us out of the while.

                if (go_declared):
                    # Instruct the next_to_play to try to play out to 31
                    match next_to_play:
                        case CribbageRole.PLAYER:
                            prefix  = 'After go declared by Dealer'
                            # Capture player score before play strategy GO call
                            pre_go_score = self._player_score
                            # Try/Except requrired in case call to self.peg_for_player ends game.
                            try:
                                count = self._player_play_strategy.go(go_round_count, self.play_card_for_player, self.get_player_hand,
                                                                      self.get_combined_play_pile, self.determine_score_playing, self.peg_for_player,
                                                                      self.record_play)
                            except CribbageGameOverError as e:
                                # (except covered by unit test)
                                # Dig go_play_score out of e, and add it to deal_info
                                deal_info.player_play_score += e.go_play_score
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                # TODO: Should I feed go_play_score into the new exception?
                                raise CribbageGameOverError('Game ended when player scored a combination during GO', deal_info = deal_info)
                            # Need to handle adding any play score during play strategy GO to deal_info
                            deal_info.player_play_score += (self._player_score - pre_go_score)
                            # Score 1 or 2 for the player, depending on how the player played out the go
                            go_round_count += count
                            if (go_round_count) == 31:
                                deal_info.player_play_score += 2
                                # Build a CribbageComboInfo object to explain the reason for scoring
                                reason = CribbageComboInfo()
                                reason.combo_name='Go 31'
                                reason.number_instances=1
                                reason.score=2
                                reason.instance_list=[self._combined_pile.get_cards()]
                                try:
                                    self.peg_for_player(2, [reason], during=CribbageDealPhase.PLAYING_DEAL)
                                except CribbageGameOverError as e:
                                    # (except covered by unit test)
                                    # Output the play record to facilitate unit test creation
                                    logger.debug(f"Play record: {self._recorded_play}")
                                    # Raise a new CribbageGameOverError with the added deal_info
                                    raise CribbageGameOverError('Game ended when player scored after GO', deal_info = deal_info)
                            else:
                                deal_info.player_play_score += 1
                                # Build a CribbageComboInfo object to explain the reason for scoring
                                reason = CribbageComboInfo()
                                reason.combo_name='Go <31'
                                reason.number_instances=1
                                reason.score=1
                                reason.instance_list=[self._combined_pile.get_cards()]
                                try:
                                    self.peg_for_player(1, [reason], during=CribbageDealPhase.PLAYING_DEAL)
                                except CribbageGameOverError as e:
                                    # (except covered by unit test)
                                    # Output the play record to facilitate unit test creation
                                    logger.debug(f"Play record: {self._recorded_play}")
                                    # Raise a new CribbageGameOverError with the added deal_info
                                    raise CribbageGameOverError('Game ended when player scored after GO', deal_info = deal_info)

                            # Rotate who will play next
                            next_to_play = CribbageRole.DEALER
                        case CribbageRole.DEALER:
                            prefix  = 'After go declared by Player'
                            # Capture dealer score before play strategy GO call
                            pre_go_score = self._dealer_score
                            # Try/Except requrired in case call to self.peg_for_dealer ends game.
                            try:
                                count = self._dealer_play_strategy.go(go_round_count, self.play_card_for_dealer, self.get_dealer_hand,
                                                                      self.get_combined_play_pile, self.determine_score_playing, self.peg_for_dealer,
                                                                      self.record_play)
                            except CribbageGameOverError as e:
                                # Dig go_play_score out of e, and add it to deal_info
                                deal_info.dealer_play_score += e.go_play_score
                                # (except covered by unit test)
                                # Output the play record to facilitate unit test creation
                                logger.debug(f"Play record: {self._recorded_play}")
                                # Raise a new CribbageGameOverError with the added deal_info
                                # TODO: Should I feed go_play_score into the new exception?
                                raise CribbageGameOverError('Game ended when dealer scored a combination during GO', deal_info = deal_info)
                            # Need to handle adding any play score during play strategy GO to deal_info
                            deal_info.dealer_play_score += (self._dealer_score - pre_go_score)
                            # Score 1 or 2 for the dealer, depending on how the dealer played out the go
                            go_round_count += count
                            if (go_round_count) == 31:
                                deal_info.dealer_play_score += 2
                                # Build a CribbageComboInfo object to explain the reason for scoring
                                reason = CribbageComboInfo()
                                reason.combo_name='Go 31'
                                reason.number_instances=1
                                reason.score=2
                                reason.instance_list=[self._combined_pile.get_cards()]
                                try:
                                    self.peg_for_dealer(2, [reason])
                                except CribbageGameOverError as e:
                                    # (except covered by unit test)
                                    # Output the play record to facilitate unit test creation
                                    logger.debug(f"Play record: {self._recorded_play}")
                                    # Raise a new CribbageGameOverError with the added deal_info
                                    raise CribbageGameOverError('Game ended when dealer scored after GO', deal_info = deal_info)
                            else:
                                deal_info.dealer_play_score += 1
                                # Build a CribbageComboInfo object to explain the reason for scoring
                                reason = CribbageComboInfo()
                                reason.combo_name='Go <31'
                                reason.number_instances=1
                                reason.score=1
                                reason.instance_list=[self._combined_pile.get_cards()]
                                try:
                                    self.peg_for_dealer(1, [reason], during=CribbageDealPhase.PLAYING_DEAL)
                                except CribbageGameOverError as e:
                                    # (except covered by unit test)
                                    # Output the play record to facilitate unit test creation
                                    logger.debug(f"Play record: {self._recorded_play}")
                                    # Raise a new CribbageGameOverError with the added deal_info
                                    raise CribbageGameOverError('Game ended when dealer scored after GO', deal_info = deal_info)
                            # Rotate who will play next
                            next_to_play = CribbageRole.PLAYER
                    self.log_play_info(prefix, go_round_count)
                    self.log_pegging_info()
                    continue # Get us out of the while.
            
                # If go has not been declared, then continuing alternating follows, until go is declared, or we run out of cards in both hands
                # That is, the while should keep cycling
                # end of while not go_declared:
        
        # Play continues until both dealer and player are out of cards.
        # end of while dealer or player have cards left in their hand
            
        # It's time to show (that is, count the hands after playing). During play, the hands have been emptied into the play piles, so score the piles.
 
        # Score the player's hand
        logger.info(f"Showing player hand: {str(self._player_pile)}")
        reasons = []
        score = self.determine_score_showing_hand(self._player_pile, starter, reasons)
        logger.info(f"     Total player score from showing hand: {score}")
        deal_info.player_show_score += score
        try:
            self.peg_for_player(score, reasons, during=CribbageDealPhase.SHOWING_HAND)
        except CribbageGameOverError as e:
            # (except covered by unit test)
            # Output the play record to facilitate unit test creation
            logger.debug(f"Play record: {self._recorded_play}")
            # Raise a new CribbageGameOverError with the added deal_info
            raise CribbageGameOverError('Game ended while showing player hand', deal_info = deal_info)
 
        # Score the dealer's hand
        logger.info(f"Showing dealer hand: {str(self._dealer_pile)}")
        reasons = []
        score = self.determine_score_showing_hand(self._dealer_pile, starter, reasons)
        logger.info(f"     Total dealer score from showing hand: {score}")
        deal_info.dealer_show_score += score
        try:
            self.peg_for_dealer(score, reasons, during=CribbageDealPhase.SHOWING_HAND)
        except CribbageGameOverError as e:
            # (except covered by unit test)
            # Output the play record to facilitate unit test creation
            logger.debug(f"Play record: {self._recorded_play}")
            # Raise a new CribbageGameOverError with the added deal_info
            raise CribbageGameOverError('Game ended while showing dealer hand', deal_info = deal_info)
        
        # Score the dealer's crib
        logger.info(f"Showing dealer crib: {str(self._crib_hand)}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_CRIB,  crib=str(self._crib_hand)))
        reasons = []
        score = self.determine_score_showing_crib(self._crib_hand, starter, reasons)
        logger.info(f"     Total dealer score from showing crib: {score}")
        deal_info.dealer_crib_score += score
        try:
            self.peg_for_dealer(score, reasons, during=CribbageDealPhase.SHOWING_CRIB)
        except CribbageGameOverError as e:
            # (except covered by unit test)
            # Output the play record to facilitate unit test creation
            logger.debug(f"Play record: {self._recorded_play}")
            # Raise a new CribbageGameOverError with the added deal_info
            raise CribbageGameOverError('Game ended while showing crib', deal_info = deal_info)
        
        self.log_pegging_info()
        
        # Output the play record to facilitate unit test creation
        logger.debug(f"Play record: {self._recorded_play}")

        return deal_info