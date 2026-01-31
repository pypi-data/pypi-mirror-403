"""
Defines the CribbageSimulator class, which actually has little responsibility. Conceptually it is a level above CribbageGame,
with the idea that it could be used to have multiple games played automatically, for example to generate game-play statistics.
Right now it's utility is to set up logging.

Note that logging is critical because it is the mechanism that provides output to the console for the user to see.

Exported Classes:
    CribbageSimulator: Defines setup_logging(...) method to configure logging for a cribbage game.

Exported Exceptions:
    None    
 
Exported Functions:
    None

Logging:
    A logger named 'cribbage_logger' is created and configured in CribbageSimulator.setup_logging(...).
    It logs to stderr through a stream handler. Default logging level is logging.INFO, but can be set to logging.DEBUG by passing
    debug=True in method call.
    
    If queue=<Queue object> is passed into the method call, then a queue handler will also be set up, and could then be
    used by a tkAppFramework.tkSimulatorApp implementation to capture game output.
 """


# Standard imports
import logging
from logging.handlers import QueueHandler as QueueHandler
import sys

# Local imports


class CribbageSimulator:

    """
    This class does very little currently. Conceptually it is a level above CribbageGame, with the idea that it could be used to have multiple
    games played automatically, for example to generate game-play statistics. Right now it's utility is to set up logging.
    """
    def setup_logging(self, debug = False, queue = None):
        """
        This method configures logging. It should be called ahead of any calls to CribbageGame.play() or CribbageDeal.play() to ensure the
        expected behavior of logging. Though failure to do so should not be breaking.
        :parameter debug: If True, then logger level set to DEBUG (and hidden information will be revealed in output), boolean
        :parameter queue: If is not None, then a queue handler will be set up with this queue. Queue object
        :return: None
        """
        # Create a logger with name 'cribbage_logger'. This is NOT the root logger, which is one level up from here, and has no name.
        # This logger is currently intended to handle everything that isn't form_crib, follow, or go data going to file, like for AI training.
        logger = logging.getLogger('cribbage_logger')
        # This is the threshold level for the logger itself, before it will pass to any handlers, which can have their own threshold.
        # Should be able to control here what the stream handler receives and thus what ends up going to stderr.
        # Use this key for now:
        #   DEBUG = debug messages sent to this logger would end up on stderr, but see below where this is changed (e.g., hidden information like
        #           an automatic player's dealt hand)
        #   INFO = info messages sent to this logger would end up on stderr, but see below where this is changed
        #           (e.g., all the scattered output to screen an interactive user needs to understand what is happening)
        if not debug:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
        # Set up this highest level below root logger with a stream handler
        # The stream handler logs to sys.stdout, not the default of sys.stderr, so that, I hope, interlaces appropriately withs prints
        sh = logging.StreamHandler(stream=sys.stdout)
        # Set the threshold for the stream handler itself, which will come into play only after the logger threshold is met.
        sh.setLevel(logging.DEBUG)
        # Add the stream handler to the logger
        logger.addHandler(sh)

        # if argument queue is not None, then set up the highest level below root logger with a QueueHandler
        if queue is not None:
            qh = QueueHandler(queue)
            # Set the threshold for the queue handler itself, which will come into play only after the logger threshold is met.
            qh.setLevel(logging.DEBUG)
            # Add the queue handler to the logger
            logger.addHandler(qh)
    
        # Create the new logger that will handle form_crib/follow/go data going to file.
        # Create it as a child of the logger, 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger.crib_follow_go_logger')
        # Set the logger's level to INFO. If this is left at the NOTSET default, then all messages would be sent to parent
        # (Except that propagate is set to False below.) 
        logger.setLevel(logging.INFO)
        # Don't propagate to parents from this logger
        logger.propagate = False
        
        return None