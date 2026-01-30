"""
The functions in this module execute various use cases of the cribbage game simulator. 

Exported Classes:
    None

Exported Exceptions:
    None
 
Exported Functions:
    play_interactive_game() - Human user plays interactive cribbage game against computer player.
    play_interactive_deal() - Human user plays one cribbage deal against computer player.
    play_auto_game() - Automatically plays one game of cribbage with two computer players.
    play_auto_deal() - Automaticaly plays one cribbage deal with two computer players.
    __main__ -- Query user for a use case, and then call the appropriate function.
"""

# Standard imports


# Local imports
from CribbageSim.CribbagePlayStrategy import InteractiveCribbagePlayStrategy, HoyleishDealerCribbagePlayStrategy, HoyleishPlayerCribbagePlayStrategy
from CribbageSim.CribbageDeal import CribbageDeal
from CribbageSim.CribbageGame import CribbageGame
from CribbageSim.CribbageSimulator import CribbageSimulator
from UserResponseCollector.UserQueryCommand import UserQueryCommandMenu
import UserResponseCollector.UserQueryReceiver


def play_interactive_game():
    """
    Use CribbageSimulator to play an interactive game as player 1.
    :return: None
    """
    
    # Ask user if they want to unshelve a shelved game
    receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
    query_preface = 'Do you want to start a new game, or reload a saved game?'
    query_dic = {'n':'New Game', 's':'Saved Game'}
    command = UserQueryCommandMenu(receiver, query_preface, query_dic)
    response = command.Execute()
    match response:
        case 'n':
            load_game = False
        case 's':
            load_game = True

    print('You are playing a game as player 1, against a machine player 2.')
    game = CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                        dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
    game.play(load_game)

    return None

def play_interactive_deal():
    """
    Use CribbageSimulator to play an interactive deal, as the dealer.
    :return: None
    """

    print('You are playing a deal as the dealer, against a machine player.')
    deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), InteractiveCribbagePlayStrategy())
    deal.play()

    return None

def play_auto_game():
        """
        Use CribbageSimulator to play a completely automatic game.
        :return: None
        """
        
        game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                            dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
        game.play()
        
        return None

def play_auto_deal():
    """
    Use CribbageSimulator to play a completely automatic deal.
    :return: None
    """
    # Seed the random number generator
    from random import seed
    seed(1234567890)

    deal = CribbageDeal(HoyleishPlayerCribbagePlayStrategy(), HoyleishDealerCribbagePlayStrategy())
    deal.play()
    
    return None

def play_debug():
    """
    Use CribbageSimulator to set up and execute a debugging scenario.
    :return: None
    """

    # Seed the primary random number generator
    from random import seed
    my_seed = 1234567890
    print(f"Seed Value: {my_seed}")
    seed(my_seed)

    # game = CribbageGame(player_strategy1 = RandomCribbagePlayStrategy(), player_strategy2 = RandomCribbagePlayStrategy())
    game = CribbageGame(player_strategy1 = HoyleishPlayerCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                dealer_strategy1 = HoyleishDealerCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
    # game = CribbageGame(player_strategy1 = RandomCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
    #                 dealer_strategy1 = RandomCribbagePlayStrategy(), dealer_strategy2 = HoyleishDealerCribbagePlayStrategy())
    return_val = game.play()

    return None


if __name__ == '__main__':
    
    """
    Query the user for how they wish to use the Cribage simulator, and then launch that usage.
    This includes a "debug" usage to set up what ever situation is needed for debugging, since I can't seem to reliably debug unit tests.
    """
    
    # Set up logging
    CribbageSimulator().setup_logging(False)
    
    print('---------------------------------')
    print('*** Python Cribbage Simulator ***')
    print('---------------------------------')
        
    # Build a query for the user to obtain their choice of how to user the simulator
    receiver = UserResponseCollector.UserQueryReceiver.UserQueryReceiver_GetCommandReceiver()
    query_preface = 'How do you want to use the simulator?'
    query_dic = {'q':'Quit', 'g':'Interactive Game', 'i':'Interactive Deal', 'a':'Automatic Game', 'b':'Automatic Deal', 'd':'Debug'}
    command = UserQueryCommandMenu(receiver, query_preface, query_dic)
    response = command.Execute()
    
    while response != 'q':
        
        match response:
            
            case 'g':
                play_interactive_game()
            
            case 'i':
                play_interactive_deal()
            
            case 'a':
                play_auto_game()

            case 'b':
                play_auto_deal()

            case 'd':
                play_debug()
        
        print('--------------------')
        response = command.Execute()
      