"""
Defines the CribbageGame class, which represents a cribbage game to be played by two players.

Exported Classes:
    CribbageGameInfo - Used to return information about the results of a cribbage game from CribbageGame.play(...).
    CribbageGame: Represents a cribbage game, to be played out by two players, player1 and player2.

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
import os
import json

# Local imports
from CribbageSim.CribbageBoard import CribbageBoard
from CribbageSim.CribbageDeal import CribbageDeal, CribbagePlayers
from CribbageSim.CribbagePlayStrategy import CribbagePlayStrategy, InteractiveCribbagePlayStrategy, HoyleishPlayerCribbagePlayStrategy
from CribbageSim.exceptions import CribbageGameOverError
from CribbageSim.CribbageGameOutputEvents import CribbageGameOutputEvents, CribbageGameLogInfo, CribbageDealPhase
from UserResponseCollector.UserQueryCommand import UserQueryCommandPathOpen, UserQueryCommandPathSave
import UserResponseCollector.UserQueryReceiver


class CribbageGameInfo:
    """
    A class with all members/attributes considered public. Used to return information about the results of a cribbage game,
    from CribbageGame.play(...).
    """
    def __init__(self):
        """
        Create and initialize attributes.
        """
        self.player1_total_play_score = 0
        self.player1_total_his_heals_score = 0 # Starter card was a J
        self.player1_total_show_score = 0
        self.player1_total_crib_score = 0
        self.player2_total_play_score = 0
        self.player2_total_his_heals_score = 0 # Starter card was a J
        self.player2_total_show_score = 0
        self.player2_total_crib_score = 0
        self.winning_player = ''
        self.winning_player_final_score = 0
        self.losing_player_final_score = 0
        self.deals_in_game = 0
 

class CribbageGame:
    """
    Class representing a cribbage game, to be played out by two players, player1 and player2.
    """
    
    def __init__(self, name1 = 'human_player', name2 = 'machine_player',
                 player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                 dealer_strategy1 = None, dealer_strategy2 = None):
        """
        Construct a cribbage game with a CribbageBoard, two player names, and a CribbageDeal.
        :parameter name1: Name of player1, string
        :parameter name2: Name of player2, string
        :parameter player_strategy1: Player strategy for player1, Instance of CribbagePlayStrategy
        :parameter player_strategy2: Player strategy for player2, Instance of CribbagePlayStrategy
        :parameter dealer_strategy1: Dealer strategy for player1 (defaults to player_strategy1 if None), Instance of CribbagePlayStrategy
        :parameter dealer_strategy2: Dealer strategy for player2 (defaults to player_strategy2 if None), Instance of CribbagePlayStrategy
        """
        assert(isinstance(player_strategy1, CribbagePlayStrategy))
        assert(isinstance(player_strategy2, CribbagePlayStrategy))
        if dealer_strategy1: assert(isinstance(dealer_strategy1, CribbagePlayStrategy))
        if dealer_strategy2: assert(isinstance(dealer_strategy2, CribbagePlayStrategy))
        self._board = CribbageBoard()
        self._player1 = name1
        self._player2 = name2
        self._player1_player_strategy = player_strategy1
        if dealer_strategy1: 
            self._player1_dealer_strategy = dealer_strategy1
        else:
            self._player1_dealer_strategy = player_strategy1
        self._player2_player_strategy = player_strategy2
        if dealer_strategy2: 
            self._player2_dealer_strategy = dealer_strategy2
        else:
            self._player2_dealer_strategy = player_strategy2
        self._deal = CribbageDeal(self._player2_player_strategy, self._player1_dealer_strategy)
        self._next_to_deal = CribbagePlayers.PLAYER_1
        self._deal_count = 0
        self._game_stats = CribbageGameInfo()

    def get_player1_name(self):
        """
        :return: Name of player1, string
        """
        return self._player1
    
    def get_player2_name(self):
        """
        :return: Name of player2, string
        """
        return self._player2
    
    def get_player_scores(self):
        """
        :return: (player1 score, player2 score), tuple
        """
        return self._board.get_scores()
        
    def peg_for_player1(self, count = 1, reason = [], during = CribbageDealPhase.NO_PHASE):
        """
        Peg on the board count for player1.
        :parameter count: The count to peg for player1 on the board, int
        :parameter reason: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: Current peg total for player1 after pegging count, int
        """
        return self._board.peg_for_player1(count, reason, during)
        
    def peg_for_player2(self, count = 1, reason = [], during = CribbageDealPhase.NO_PHASE):
        """
        Peg on the board count for player2.
        :parameter count: The count to peg for player2 on the board, int
        :parameter reason: Why the points are being pegged, list of CribbageComboInfo objects
        :parameter during: Optional value indicating during which phase of a deal the pegging is occurring, as CribbageDealPhase Enum
        :return: Current peg total for player2 after pegging count, int
        """
        return self._board.peg_for_player2(count, reason, during)
        
    def play(self, load_game=False):
        """
        Play a game of cribbage.
        :parameter load_game: Should we load a shelved game? as Boolean
        :return: Information about the results of the game, CribbageGameInfo object
        """

        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')
        
        if load_game:
            # Load a shelved game
            logger.info(f"Restarting a saved game of cribbage with {self._player1} vs {self._player2}.",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.START_GAME, name_player1=self._player1,
                                                  name_player2=self._player2))
            self.un_shelve_game()
        else:
            # Start a new game
            logger.info(f"Starting a new game of cribbage with {self._player1} vs {self._player2}.",
                        extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.START_GAME, name_player1=self._player1,
                                                  name_player2=self._player2))
            self._deal_count = 0
            # TODO: For now player1 will always deal first, but implement random selection, such as cutting for high card
            # Consider that this predictability is beneficial to unit testing.
            self._next_to_deal = CribbagePlayers.PLAYER_1

        game_over = False
        
        while not game_over:
        
            self._deal_count += 1

            # Reset deal so we are ready for a new deal
            match self._next_to_deal:
                case CribbagePlayers.PLAYER_1:
                    logger.info(f"Player {self._player1} will deal.",
                                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.START_DEAL, name_dealer=self._player1))
                    self._deal.reset_deal(self.peg_for_player2, self.peg_for_player1, player_participant=CribbagePlayers.PLAYER_2,
                                          dealer_participant=CribbagePlayers.PLAYER_1)
                    # Set the correct strategies for player and dealer
                    self._deal.set_player_play_strategy(self._player2_player_strategy)
                    self._deal.set_dealer_play_strategy(self._player1_dealer_strategy)
                    self._next_to_deal = CribbagePlayers.PLAYER_2
                case CribbagePlayers.PLAYER_2:
                    logger.info(f"Player {self._player2} will deal.",
                                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.START_DEAL, name_dealer=self._player2))
                    self._deal.reset_deal(self.peg_for_player1, self.peg_for_player2, player_participant=CribbagePlayers.PLAYER_1,
                                          dealer_participant=CribbagePlayers.PLAYER_2)
                    # Set the correct strategies for player and dealer
                    self._deal.set_player_play_strategy(self._player1_player_strategy)
                    self._deal.set_dealer_play_strategy(self._player2_dealer_strategy)
                    self._next_to_deal = CribbagePlayers.PLAYER_1
            
            # Play the current deal
            try:
                deal_info = self._deal.play()
                # Accumulate deal results info into game results info
                match self._next_to_deal:
                    case CribbagePlayers.PLAYER_1:
                        # Since we already rotated next_to_deal above, Player_1 was the player for the deal we just played
                        self._game_stats.player1_total_play_score += deal_info.player_play_score
                        self._game_stats.player1_total_show_score += deal_info.player_show_score
                        self._game_stats.player2_total_play_score += deal_info.dealer_play_score
                        self._game_stats.player2_total_his_heals_score += deal_info.dealer_his_heals_score
                        self._game_stats.player2_total_show_score += deal_info.dealer_show_score
                        self._game_stats.player2_total_crib_score += deal_info.dealer_crib_score
                    case CribbagePlayers.PLAYER_2:
                        # Since we already rotated next_to_deal above, Player_1 was the dealer for the deal we just played
                        self._game_stats.player2_total_play_score += deal_info.player_play_score
                        self._game_stats.player2_total_show_score += deal_info.player_show_score
                        self._game_stats.player1_total_play_score += deal_info.dealer_play_score
                        self._game_stats.player1_total_his_heals_score += deal_info.dealer_his_heals_score
                        self._game_stats.player1_total_show_score += deal_info.dealer_show_score
                        self._game_stats.player1_total_crib_score += deal_info.dealer_crib_score
            except CribbageGameOverError as e:
                # Log why the game ended, for example, that it ended while the crib was being shown. This information is obtained from the exception.
                logger.info(e.args[0])
                # Accumulate deal info for last deal of the game into game info, because it will not have happened above, due to the exception ending the game.
                (p1_score, p2_score) = self._board.get_scores()
                if p1_score == 121:
                    self._game_stats.winning_player = self._player1
                    self._game_stats.winning_player_final_score = p1_score
                    self._game_stats.losing_player_final_score = p2_score
                    self._game_stats.deals_in_game = self._deal_count
                    logger.info(f"Player {self._player1} wins the game.")
                else:
                    self._game_stats.winning_player = self._player2
                    self._game_stats.winning_player_final_score = p2_score
                    self._game_stats.losing_player_final_score = p1_score
                    self._game_stats.deals_in_game = self._deal_count
                    logger.info(f"Player {self._player2} wins the game.")
                # Handle accumulating deal info that arrived in CribbageGameOverError into game info
                match self._next_to_deal:
                    case CribbagePlayers.PLAYER_1:
                        # Since we already rotated next_to_deal above, Player_1 was the player for the deal we just played
                        self._game_stats.player1_total_play_score += e.deal_info.player_play_score
                        self._game_stats.player1_total_show_score += e.deal_info.player_show_score
                        self._game_stats.player2_total_play_score += e.deal_info.dealer_play_score
                        self._game_stats.player2_total_his_heals_score += e.deal_info.dealer_his_heals_score
                        self._game_stats.player2_total_show_score += e.deal_info.dealer_show_score
                        self._game_stats.player2_total_crib_score += e.deal_info.dealer_crib_score
                    case CribbagePlayers.PLAYER_2:
                        # Since we already rotated next_to_deal above, Player_1 was the dealer for the deal we just played
                        self._game_stats.player2_total_play_score += e.deal_info.player_play_score
                        self._game_stats.player2_total_show_score += e.deal_info.player_show_score
                        self._game_stats.player1_total_play_score += e.deal_info.dealer_play_score
                        self._game_stats.player1_total_his_heals_score += e.deal_info.dealer_his_heals_score
                        self._game_stats.player1_total_show_score += e.deal_info.dealer_show_score
                        self._game_stats.player1_total_crib_score += e.deal_info.dealer_crib_score
                break
        
            except UserResponseCollector.UserQueryReceiver.UserQueryReceiverTerminateQueryingThreadError as e:
                # For now, do nothing but (1) Log that game terminated early, and (2) return a default CribbageGameInfo object
                # TODO: Investigate any problems
                logger.info(f"Cribbage game terminating in the middle of play, at request of user.")
                return CribbageGameInfo()

            # Log end of deal board
            logger.info(f"After deal {str(self._deal_count)}:\n{str(self._board)}")

            # Query player 1 (since in a human/machine game, player 1 will be the human) play strategy
            # if we should save the current state of the game and end play, or if we should continue to the next deal.
            match self._next_to_deal:
                case CribbagePlayers.PLAYER_1:
                    # Since we already rotated next_to_deal above, Player_1 was the player for the deal we just played
                    response = self._player1_player_strategy.continue_save_end()
                case CribbagePlayers.PLAYER_2:
                    # Since we already rotated next_to_deal above, Player_1 was the dealer for the deal we just played
                    response = self._player1_dealer_strategy.continue_save_end()
            match response:
                case (True, False): # Continue play
                    pass
                case (False, True): # Stop play, save game state
                    # For now, do nothing but (1) Log that game terminated early, and (2) return a default CribbageGameInfo object
                    # TODO: Investigate any problems
                    self.shelve_game()
                    logger.info(f"Cribbage game terminating at end of deal, at request of player 1.",
                                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.END_GAME))
                    return CribbageGameInfo()
                case (False, False): # Stop play, do NOT save game state
                    # For now, do nothing but (1) Log that game terminated early, and (2) return a default CribbageGameInfo object
                    # TODO: Investigate any problems
                    logger.info(f"Cribbage game terminating at end of deal, at request of player 1.",
                                extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.END_GAME))
                    return CribbageGameInfo()
 
        # Log end of game results
        logger.info(f"At game end, after {self._deal_count} deals:\n{str(self._board)}",
                    extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.END_GAME, name_winner=self._game_stats.winning_player))
        logger.info(f"     Winning Player: {self._game_stats.winning_player}")
        logger.info(f"     Winning Player Final Score: {self._game_stats.winning_player_final_score}")
        logger.info(f"     Losing Player Final Score: {self._game_stats.losing_player_final_score}")
        logger.info(f"Statistics for {self._player1}:")
        logger.info(f"     Total Play Score: {self._game_stats.player1_total_play_score}")
        logger.info(f"     Total His Heals Score: {self._game_stats.player1_total_his_heals_score}")
        logger.info(f"     Total Show Score: {self._game_stats.player1_total_show_score}")
        logger.info(f"     Total Crib Score: {self._game_stats.player1_total_crib_score}")
        logger.info(f"     Check Sum: {self._game_stats.player1_total_play_score + self._game_stats.player1_total_his_heals_score + self._game_stats.player1_total_show_score + self._game_stats.player1_total_crib_score}")
        logger.info(f"Statistics for {self._player2}:")
        logger.info(f"     Total Play Score: {self._game_stats.player2_total_play_score}")
        logger.info(f"     Total His Heals Score: {self._game_stats.player2_total_his_heals_score}")
        logger.info(f"     Total Show Score: {self._game_stats.player2_total_show_score}")
        logger.info(f"     Total Crib Score: {self._game_stats.player2_total_crib_score}")
        logger.info(f"     Check Sum: {self._game_stats.player2_total_play_score + self._game_stats.player2_total_his_heals_score + self._game_stats.player2_total_show_score + self._game_stats.player2_total_crib_score}")

        return self._game_stats

    def writeGameToFile(self, file, filetype) -> None:
        """
        Write the game data to a file-like object.
        :parameter file: A file-like object to which to write the game data.
        :parameter filetype: A string indicating the type of file (e.g., '.json', '.xml', etc.).
        :return: None
        """
        if filetype != '.json':
            raise ValueError('CribbageGame.writeGameToFile() only supports filetype ".json"')
        # Add the game data to a dictionary
        data={}
        # Boilerplate data so we know what "generator" created the file, and what the version number of the
        # schema is.
        data['archive_generator']='CribbageSimulator'
        data['archive_schema_version']=1
        # Player name data
        data['player1_name']=self.get_player1_name()
        data['player2_name']=self.get_player2_name()
        # Game state data
        data['next_to_deal']=str(self._next_to_deal)
        data['deal_count']=self._deal_count
        # Game stats data
        stats_list = dir(self._game_stats)
        for stat in stats_list:
            if not stat.startswith('__') and not stat.endswith('__'):
                key = f"game_stats_{stat}"
                value = self._game_stats.__getattribute__(stat)
                data[key]=value
        # Cribbage board data
        (cur,pre)=self._board.get_player1_status()
        data['player1_current']=cur
        data['player1_previous']=pre
        (cur,pre)=self._board.get_player2_status()
        data['player2_current']=cur
        data['player2_previous']=pre
        # Convert the data dictionary to a JSON string
        json_string = json.dumps(data)
        # Write the JSON string to the file-like object
        file.write(json_string)
        return None

    def readGameFromFile(self, file, filetype) -> None:
        """
        Read the game data from a file-like object.
        :parameter file: A file-like object from which to read the game data.
        :parameter filetype: A string indicating the type of file (e.g., '.json', '.xml', etc.).
        :return: None
        """
        # Read the JSON string from the file-like object
        if filetype != '.json':
            raise ValueError('CribbageGame.readGameFromFile() only supports filetype ".json"')
        json_string = file.read()
        # Convert the JSON string to a dictionary
        data = json.loads(json_string)
        # Check that the file we loaded was created by the expected archive generator.
        if data['archive_generator'] != 'CribbageSimulator':
            raise ValueError(f"CribbageGame.readGameFromFile() attempted to read archive created by unexpected generator {data['archive_generator']}.")
        # Map the data dictionary to the game object attributes, respecting vatiations in archive schema version.
        if data['archive_schema_version'] == 1:
            # Player name data
            self._player1=data['player1_name']
            self._player2=data['player2_name']
            # Game state data
            dealer = data['next_to_deal']
            match dealer:
                case 'CribbagePlayers.PLAYER_1':
                    self._next_to_deal=CribbagePlayers.PLAYER_1
                case 'CribbagePlayers.PLAYER_2':
                    self._next_to_deal=CribbagePlayers.PLAYER_2
            self._deal_count=data['deal_count']
            # Game stats data
            self._game_stats.player1_total_play_score=data['game_stats_player1_total_play_score']
            self._game_stats.player1_total_his_heals_score=data['game_stats_player1_total_his_heals_score']
            self._game_stats.player1_total_show_score=data['game_stats_player1_total_show_score']
            self._game_stats.player1_total_crib_score=data['game_stats_player1_total_crib_score']
            self._game_stats.player2_total_play_score=data['game_stats_player2_total_play_score']
            self._game_stats.player2_total_his_heals_score=data['game_stats_player2_total_his_heals_score']
            self._game_stats.player2_total_show_score=data['game_stats_player2_total_show_score']
            self._game_stats.player2_total_crib_score=data['game_stats_player2_total_crib_score']
            self._game_stats.winning_player=data['game_stats_winning_player']
            self._game_stats.winning_player_final_score=data['game_stats_winning_player_final_score']
            self._game_stats.losing_player_final_score=data['game_stats_losing_player_final_score']
            self._game_stats.deals_in_game=data['game_stats_deals_in_game']
            # Cribbage board data
            self._board._player1_current=data['player1_current']
            self._board._player1_previous=data['player1_previous']
            self._board._player2_current=data['player2_current']
            self._board._player2_previous=data['player2_previous']
        else:
            raise ValueError(f"CribbageGame.readGameFromFile() attempted to read archive with unexpected schema version {data['archive_schema_version']}.")
        return None 

    def shelve_game(self, path=None):
        """
        Save the game by writing it to a json file.
        :parameter path: The path to the json file. This should have a .json extension, and all backslashes should be escaped., as String
            If no path is provided, then user will be queried.
        :return None:
        """
        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        if path is None:
            receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
            query_preface = 'Where do you want to save the game? Provide the path to a .json file.'
            command = UserQueryCommandPathSave(receiver, query_preface)
            save_path = command.Execute()
            save_path = str(save_path)
        else:
            save_path = path

        logger.info(f"Saving game to path: {save_path}")

        if len(save_path)>0:
            with open(save_path, mode='w') as f:
                self.writeGameToFile(f, os.path.splitext(save_path)[1])
        
        return None

    def un_shelve_game(self, path=None):
        """
        Restore the game data by reading it from a json file.
        :parameter path: The path to the json file. This should have a .json extension, and all backslashes should be escaped., as String
            If no path is provided, then user will be queried.
        :return None:
        """

        # Get the logger 'cribbage_logger'
        logger = logging.getLogger('cribbage_logger')

        if path is None:
            receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
            query_preface = 'Which saved game do you want to open? Provide the path to a .json file.'
            command = UserQueryCommandPathOpen(receiver, query_preface)
            load_path = command.Execute()
            load_path = str(load_path)
        else:
            load_path = path

        logger.info(f"Loading game from path: {load_path}")

        if len(load_path)>0:
            with open(load_path) as f:
                self.readGameFromFile(f, os.path.splitext(load_path)[1])

        logger.info(f"Player 1 peg locations: {self._board.get_player1_status()[0]},{self._board.get_player1_status()[1]}",
            extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_SCORE_PLAYER1,
                                        score_player1=(self._board.get_player1_status()[0],self._board.get_player1_status()[1])))

        logger.info(f"Player 2 peg locations: {self._board.get_player2_status()[0]},{self._board.get_player2_status()[1]}",
            extra=CribbageGameLogInfo(event_type=CribbageGameOutputEvents.UPDATE_SCORE_PLAYER2,
                                        score_player2=(self._board.get_player2_status()[0],self._board.get_player2_status()[1])))

        return None
