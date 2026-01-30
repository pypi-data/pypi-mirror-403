"""
Defines the CribbageBoard class, which represents a cribbage board, for tracking scores for both players.

Exported Classes:
    CribbageBoard - Represents a cribbage board, for tracking scores for both players.

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

# Local imports
from CribbageSim.CribbageCombination import CribbageComboInfo
from CribbageSim.exceptions import CribbageGameOverError
from CribbageSim.CribbageGameOutputEvents import CribbageGameOutputEvents, CribbageGameLogInfo, CribbageDealPhase


class CribbageBoard(object):
    """
    Represents a cribbage board, so that progress through the game can be kept for both players.
    """
    
    def __init__(self):
        """
        Construct a cribbage board.
        """
        # x_current = the peg position of the leading peg, that is, the current score
        # x_previous = the peg position of the traling peg, that is the score prior to the latest pegging 
        self._player1_current = 0
        self._player1_previous = 0
        self._player2_current = 0
        self._player2_previous = 0
    
    def _make_reasons_string(self, reasons=[]):
        """
        Utility function that converts a list of CribbageComboInfo objects to a string.
        :parameter reasons: List of CribbageComboInfo objects
        :return reasons_string: A string representing the list of reasons
        """
        reasons_string=''
        for reason in reasons:
            reasons_string += f"{str(reason)}\n"
        return reasons_string

    def peg_for_player1(self, points = 1, reasons = [], during = CribbageDealPhase.NO_PHASE):
        """
        Peg the argument points for player 1, by leapfrogging the trailing peg points number of holes past the leading peg.
        :parameter points: The number of points to peg, int
        :parameter reasons: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: The current score for player 1, after pegging points, int
        """
        assert(points>0)
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        # If a reason wasn't provided in the argument, add a default 'none' one to the list
        if len(reasons)==0: reasons=[CribbageComboInfo()]

        self._player1_previous = self._player1_current
        self._player1_current += points
        if self._player1_current >= 121:
            self._player1_current = 121
            raise CribbageGameOverError
        logger.info(f"Player 1 peg locations: {self._player1_current},{self._player1_previous} After pegging:\n{self._make_reasons_string(reasons)}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_SCORE_PLAYER1,
                                              score_player1=(self._player1_current,self._player1_previous),
                                              score_record=reasons, score_while=str(during)))
        return self._player1_current
        
    def peg_for_player2(self, points = 1, reasons = [], during = CribbageDealPhase.NO_PHASE):
        """
        Peg the argument points for player 2, by leapfrogging the trailing peg points number of holes past the leading peg.
        :parameter points: The number of points to peg, int
        :parameter reasons: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: The current score for player 2, after pegging points, int
        """
        assert(points>0)
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')
        
        # If a reason wasn't provided in the argument, add a default 'none' one to the list
        if len(reasons)==0: reasons=[CribbageComboInfo()]

        self._player2_previous = self._player2_current
        self._player2_current += points
        if self._player2_current >= 121:
            self._player2_current = 121
            raise CribbageGameOverError
        logger.info(f"Player 2 peg locations: {self._player2_current},{self._player2_previous} After pegging:\n{self._make_reasons_string(reasons)}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_SCORE_PLAYER2,
                                              score_player2=(self._player2_current,self._player2_previous),
                                              score_record=reasons, score_while=str(during)))
        return self._player2_current
    
    def get_scores(self):
        """
        Return the current scores for both players.
        :return: (player 1 score, player 2 score), tuple
        """
        return (self._player1_current, self._player2_current)
    
    def get_player1_status(self):
        """
        Return the location of both leading and trailing pegs for player 1.
        :return: (Leading peg location, Trailing peg location), tuple
        """
        return (self._player1_current, self._player1_previous)
    
    def get_player2_status(self):
        """
        Return the location of both leading and trailing pegs for player 2.
        :return: (Leading peg location, Trailing peg location), tuple
        """
        return (self._player2_current, self._player2_previous)
    
    def __str__(self):
        """
        Return a string representing the current state of the board.
        """
        s = f"Player 1: Current = {self._player1_current}, Previous = {self._player1_previous}\n"
        s += f"Player 2: Current = {self._player2_current}, Previous = {self._player2_previous}"
        return s
