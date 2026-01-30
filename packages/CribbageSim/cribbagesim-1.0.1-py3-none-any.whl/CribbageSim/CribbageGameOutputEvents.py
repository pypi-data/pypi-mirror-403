"""
Defines a couple of classes used to provide "structured" output of results during game play. This structured information
could, for example, be used by a GUI to provide visual updates to the user of game results.

Exported Classes:
    CribbageGameOutputEvents - Enumerated list of output (results) events during a cribbage game.
    CribbageDealPhase - Enumerated list of phases within a deal of a cribbage game, used to indicate when scores are made.
    CribbageGameLogInfo - Used as objectified message when logging from GribbageGame.play().

    The following is a list of CribbageGameOutputEvents and the attributes that are expect to be provided values in CribbageGameLogInfo:
        0. NO_EVENT:
        1. START_GAME: name_player1, name_player2
        2. START_DEAL: name_dealer
        3. UPDATE_PLAYER1_HAND: hand_player1
        4. UPDATE_PLAYER2_HAND: hand_player2
        5. UPDATE_STARTER: starter 
        6. UPDATE_CRIB: crib
        7. UPDATE_PILE_COMBINED: pile_combined, go_round_count
        8. UPDATE_PLAYER1_PILE: pile_player1
        9. UPDATE_PLAYER2_PILE: pile_player2
        10. UPDATE_SCORE_PLAYER1: score_player1, score_record
        11. UPDATE_SCORE_PLAYER2: score_player2, score_record
        12. END_GAME: 

Exported Exceptions:
    None    
 
Exported Functions:
    None

Logging:
    None
"""


# Standard imports
from enum import Enum, StrEnum

# Local imports


class CribbageGameOutputEvents(Enum):
    """
    An enumeration of the output (result) events during a cribbage game.
    """
    NO_EVENT = 0 
    START_GAME = 1 
    START_DEAL = 2
    UPDATE_PLAYER1_HAND = 3
    UPDATE_PLAYER2_HAND = 4
    UPDATE_STARTER = 5
    UPDATE_CRIB = 6
    UPDATE_PILE_COMBINED = 7
    UPDATE_PLAYER1_PILE = 8
    UPDATE_PLAYER2_PILE = 9
    UPDATE_SCORE_PLAYER1 = 10
    UPDATE_SCORE_PLAYER2 = 11
    END_GAME = 12 # Sent when game engine ends game.


class CribbageDealPhase(StrEnum):
    """
    An enumeration of the phases within a deal of a cribbage game, used to indicate when scores are made.
    """
    NO_PHASE = 'unknown'
    CUTTING_FOR_STARTER = 'cutting starter'
    PLAYING_DEAL = 'playing' 
    SHOWING_HAND = 'showing hand'
    SHOWING_CRIB = 'showing crib'


class CribbageGameLogInfo:
    """
    A class with all members/attributes considered public. Used as objectified message when logging. with GribbageGame.play() and below.
    """
    def __init__(self, **kwargs):
        """
        Create and initialize attributes. Which attributes are poplulated depends on event_type
        :parameter event_type: The type of output event this is created for, as CribbageGameOutputEvents Enum
        """
        self.event_type = CribbageGameOutputEvents.NO_EVENT
        self.name_player1 = ''
        self.name_player2 = ''
        self.name_dealer = ''
        self.hand_player1 = '' # String like 'KH AD 2S'
        self.hand_player2 = '' # String like 'KH AD 2S'
        self.starter = '' # String like 'KH'
        self.crib = '' # String like 'KH AD 2S JC'
        self.pile_combined = '' # String like 'KH AD 2S JC'
        self.go_round_count = 0
        self.pile_player1 = '' # String like 'KH AD 2S JC'
        self.pile_player2 = '' # String like 'KH AD 2S JC'
        self.score_player1 = None # Tuple (leading peg position as int, trailing peg position as int)
        self.score_player2 = None # Tuple (leading peg position as int, trailing peg position as int)
        self.score_record = [] # List of CribbageComboInfo objects associated with the score
        self.score_while = '' # String describing what was happening when the score was made, like 'playing", 'showing hand', 'showing crib'

        # Now process any kwargs to populate some of the attributes
        for k,v in kwargs.items():
            try:
                self[k]
                setattr(self,k,v)
            except KeyError:
                continue

    def __str__(self):
        """
        In order to support standard logging, such as to a StreamHandler, just return self.message, as string
        """
        return str(self.event_type)

    def __getitem__(self,key):
        """
        So that instance[key] works and instance is iterable.
        """
        item_list =  [item_value for item_key, item_value in self.__dict__.items() if item_key == key]
        if len(item_list) == 0:
            raise KeyError(f"Key = {key} not present in CribbageGameLogInfo instance")
        value = item_list[0]
        return value

    def __iter__(self):
        return iter(self.__dict__)


# (1) Start a new game (names of players, who will deal first, reset board score to 0-0)
#     information sent: name player1 (string), name player2 (string)
#     actions taken: update player names in UI, set board score to 0-0 in UI
#     Note: Should we query for player names?
# (2) Start a new deal (which player will deal, clear hands, starter, crib, play piles, go round count)
#     information sent: name of player who will deal (string)
#     actions taken: update dealer name in UI, clear hands / crib / starter / play piles / go round count in UI
# (3) Update Hand(s)
#     information sent: Cards in hand (string, like 'KH AD 2S JC 5H 4H')
#     actions taken: Update Hand(s) in UI
# (4) Update Starter
#     information sent: card drawn as starter (string, like '7H')
#     actions taken: Update starter card in UI
# (5) Update Crib (not sent until time to show crib?)
#     information sent: Cards in crib (string, like '2S JC 5H 4H')
#     actions taken: Update Crib in UI
# (6) Update Combined Play Pile (and count for go round, with option to clear the play pile and zero the count)
#     information sent: card to add to combined pile (string, like '7H'), updated go round count (int)
#     actions taken: Update combined pile in UI, update go round count in UI
# (7) Update player play pile (may not need this)
#     information sent: card to add to player play pile (string, like '7H')
#     actions taken: Update player play pile in UI
# (8) Update dealer play pile (may not need this)
#     information sent: card to add to dealer play pile (string, like '7H')
#     actions taken: Update dealer play pile in UI
# (9) Update player score (including event, like comobo score during play, reaching 31, showing hand, ...)
#     information sent: name of player that scored (string), pegs scored (integer), score event info (dictionary?)
#     action taken: Update player score on board in UI, display score achieved and eveng info (something like 'Peg 2 for playing to 31')
# (10) Update dealer score (as for player)
#     information sent: name of player that scored (string), pegs scored (integer), score event info (dictionary?)
#     action taken: Update dealer score on board in UI, display score achieved and event info (something like 'Peg 2 for playing to 31')


