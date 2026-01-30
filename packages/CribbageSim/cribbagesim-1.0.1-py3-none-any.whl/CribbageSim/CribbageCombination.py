"""
This module defines classes representing the combinations of playing cards that score points both during 
the play of cribbage and during the showing of hands and the crib.

It defines the base class, CribbageCombination, and abstract children of that base class, CribbageCombinationPlaying
and CribbageCombinationShowing. The two abstract children follow Strategy design patterns.

Concrete implementation child classes of CribbageCombinationPlaying and CribbageCombinationShowing must:
    (1) Implement the method score(...):
        (a) For Playing, score(...) searches the play pile for the existence of scoring combinations.
        (b) For Showing, score(...) searches a hand or the crib(+starter) for the existence of scoring combinations.
    (2) Implement __init__() to set self._combo_name, and self._score_per_combo attribute values from the base class.

Exported Classes:
    CribbageComboInfo - Contains info about a particular scoring combination's presence in a cribbage hand, crib, or the play pile.
    CribbageCombination - Base class for all cribbage card scoring combinations.
    CribbageCombinationPlaying - Abstract interface for all scoring combinations during play.
        PairCombinationPlaying - Intended to search for, find, and score pairs in a cribbage play pile.
        RunCombinationPlaying - Intended to search for, find, and score runs in a cribbage play pile.
        FifteenCombinationPlaying - Intended to search for, find, and score 15's in a cribbage play pile.
    CribbageCombinationShowing - Abstract interface for all scoring combinations during play.
        PairCombination - Intended to search for, find, and score pairs in a cribbage hand.
        FlushCombination - Intended to search for, find, and score pairs in a cribbage hand, but not in the crib.
        CribFlushCombination - Intended to search for, find, and score pairs in the cribbage crib, but not in a cribbage hand.
        HisNobsCombination - Intended to search for, find, and score "his nobs" (Jack same suit as starter) in a cribbage hand.
        FifteenCombination - Intended to search for, find, and score 15's in a cribbage hand.
        RunCombination - Intended to search for, find, and score runs in a cribbage hand.

Exported Exceptions:
    None    
 
Exported Functions:
    None

Logging:
    None
"""


# Standard imports
from itertools import combinations

# Local imports
from HandsDecksCards.card import Card
from HandsDecksCards.hand import Hand


class CribbageComboInfo(object):
    """
    A class with all public members, containing information about a particular scoring combination's presence in a cribbage hand.
    """
    def __init__(self):
        """
        combo_name: The name of the cribbage scoring combination, string
        number_instances: How many times does the scoring combination appear in the cribbage hand?, int
        score: The total number of points due to all instances of teh scoring combination in the cribbage hand, int
        instance_list: List of lists of Card(s) of the instances of the scoring combination in the cribbage hand, list
        """
        self.combo_name = 'none'
        self.number_instances = 0
        self.score = 0
        self.instance_list = []
        
    def __str__(self):
        s = ''
        if self.number_instances > 0:
            s += f"{self.combo_name}: {str(self.number_instances)} for {str(self.score)}: "
            for combo in self.instance_list:
                for card in combo:
                    s += f"{str(card)} "
                s += ', '
            if len(self.instance_list) > 0:
                # Remove unneeded trailing space-comma-space
                s = s[0:len(s)-3]
        return s


# TODO: Should score() be moved up to this class, so it becomes abstract? I think I put score() at the first child level
# because the Playing version and the Showing version require different arguments.
class CribbageCombination(object):
    """
    This is the base class for cribbage card scoring combinations of types playing and showing.  It's immediate children follow strategy design
    patter and our interface classes for all cribbage card scoring combinations, either when playing or when showing a hand. It's grand children
    are the individual scoring combinations, and must implement the score(...) method of their parent. This base class provides some common attributes
    and methods for all.
    """
    def __init__(self):
        """
        Construct the base class for a cribbage scoring combination.
        _score_per_combo: The points scored for one instance of a combo in a hand, int
        """
        self._combo_name = 'none'
        self._score_per_combo = 0
        
    def get_name(self):
        """
        :return: The name of the scoring combination, e.g. 'pair', string
        """
        return self._combo_name


class CribbageCombinationPlaying(CribbageCombination):
    """
    Following a Strategy design pattern, this is the interface class for all cribbage card scoring combinations when playing a hand.
    Each child must by convention and necessity implement these methods:
        score(...) - Searches a play pile for the existence of one or more instances of the combination in the pile.
            Returns information on the istances found and the score resulting from those instances.
    The concept for using this class is that a client could hold a list of instances of children of this class, one for each scoring combination,
    and the client would iterate through that list, calling score(...) method for each one, to tally up the score after playing a card to the play pile.
    """
    def __init__(self):
        """
        Construct the base class for a cribbage scoring combination.
        """
        super().__init__()
   
    def score(self, pile = Hand()):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        :parameter pile: The play pile to search for a scoring combination, Hand object
        :return: CribbageComboInfo object with information about the scoring combination in the hand, CribbageComboInfo object
        """
        raise NotImplementedError
        return CribbageCombinInfo()


class CribbageCombinationShowing(CribbageCombination):
    """
    Following a Strategy design pattern, this is the interface class for all cribbage card scoring combinations when showing a hand.
    Each child must by convention and necessity implement these methods:
        score(...) - Searches a Hand and for the existence of one or more instances of the combination in the Hand.
            Returns information on the istances found and the score resulting from those instances.
    The concept for using this class is that a client could hold a list of instances of children of this class, one for each scoring combination,
    and the client would iterate through that list, calling score(...) method for each one, to tally up the score when showing a hand.
    """
    def __init__(self):
        """
        Construct the base class for a cribbage scoring combination.
        """
        super().__init__()

    def permutations(self, size, cards = []):
        """
        Utility function to generate all permutations of number of cards size in list cards. This utility is a critical step in searching for
        different combinations.
        :parameter size: The number of cards to include in each permutation, e.g., if size = 2, then permutations are all possible pairs, int
        :parameter cards: The list of cards to permutate, list
        :return: A list of permutations, where each permutation is a list of cards, so, a list of lists
        """
        # This if for a cribbage hand, so assert that size is 5 (hand or crib, plus starter)
        assert (size >= 2 and size <= 5)
        
        permutations = []
        
        perm_iter = combinations(cards, size)
        for perm in perm_iter:
            # Note: combinations(...) returns an iter that returns tuples. I want to return a list of lists, not a list of tuples.
            # So, list(perm) converts the tuple perm to a list.
            permutations.append(list(perm))

        return permutations
    
    def score(self, hand = Hand(), starter = None):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        :parameter hand: The hand to search for a scoring combination, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the scoring combination in the hand, CribbageComboInfo object
        """
        raise NotImplementedError
        return CribbageCombinInfo()
        

class PairCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score pairs in a cribbage hand.
    """
    
    def __init__(self):
        """
        Construct the class for pair scoring combination in cribbage hand.
        """
        self._combo_name = 'pair'
        self._score_per_combo = 2
        
    def score(self, hand = Hand(), starter = None):
        """
        Search hand for all pairs, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The hand to search for pairs, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the pairs in the hand, CribbageComboInfo object
        """
        # This is a cribbage hand, so make sure it has 4 cards ... NO ... pile during play may be more or less than 4
        # assert(hand.get_num_cards() == 4)
        
        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Add the starter card to the list of cards in the hand
        if starter is not None: cards.append(starter)
        
        # Create a list of all permutations of two cards in the hand.
        permutations = self.permutations(2, cards)
                    
        # Iterate through the permutations and determine how many of them are pairs
        for p in permutations:
            if p[0].pips == p[1].pips:
                info.number_instances += 1
                info.instance_list.append(p)
                
        # Set the score in the info object
        info.score = info.number_instances * self._score_per_combo      
        
        return info


class FlushCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score pairs in a cribbage hand, but not in the crib.
    Because ... the rules for a flush are different in a hand than in the crib.
    """
    def __init__(self):
        """
        Construct the class for pair scoring combination in cribbage hand.
        """
        self._combo_name = 'flush'
        self._score_per_combo = 4
        
    def score(self, hand = Hand(), starter = None):
        """
        Search hand for a flush, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The hand to search for a flush, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the flush in the hand, CribbageComboInfo object
        """
        # This is a cribbage hand, so make sure it has 4 cards
        # This is the correct assert to use, since flush is not a scoring combination during play, when we might not have 4 cards in the pile
        assert(hand.get_num_cards() == 4)

        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Do all cards in the hand have the same suit?
        is_flush = True
        suit = cards[0].suit
        for i in range(1, len(cards)):
            if cards[i].suit != suit:
                is_flush = False
                break;

        if is_flush:
            info.number_instances = 1
            info.instance_list = [cards]
            info.score = info.number_instances * self._score_per_combo
            
            # Check if the starter is also the same suit as the flush
            if starter and starter.suit == suit:
                info.instance_list[0].append(starter)
                info.score = info.score + 1
        
        return info


class CribFlushCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score pairs in the cribbage crib, but not in a cribbage hand.
    Because ... the rules for a flush are different in the crib than in a hand.
    """
    def __init__(self):
        """
        Construct the class for pair scoring combination in cribbage crib.
        """
        self._combo_name = 'flush'
        self._score_per_combo = 4
        
    def score(self, hand = Hand(), starter = None):
        """
        Search crib for a flush, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The crib to search for a flush, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the flush in the crib, CribbageComboInfo object
        """
        # This is a cribbage crib, so make sure it has 4 cards
        # This is the correct assert to use, since flush is not a scoring combination during play, when we might not have 4 cards in the pile
        assert(hand.get_num_cards() == 4)

        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Do all cards in the hand have the same suit?
        is_flush = True
        suit = cards[0].suit
        for i in range(1, len(cards)):
            if cards[i].suit != suit:
                is_flush = False
                break;

        if is_flush and starter.suit == suit:
            # In the crib, we only score a flush if all cards in the crib AND the starter card are of the same suit
            info.number_instances = 1
            info.instance_list = [cards]
            info.instance_list[0].append(starter)
            info.score = info.number_instances * self._score_per_combo +1
        
        return info


class HisNobsCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score "his nobs" (Jack same suit as starter) in a cribbage hand.
    """
    def __init__(self):
        """
        Construct the class for his nobs scoring combination in cribbage hand.
        """
        self._combo_name = 'his nobs'
        self._score_per_combo = 1
        
    def score(self, hand = Hand(), starter = Card()):
        """
        Search hand for his nobs, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The hand to search for a flush, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about his nobs in the hand, CribbageComboInfo object
        """
        # This is a cribbage hand, so make sure it has 4 cards
        # This is the correct assert to use, since his nobs is not a scoring combination during play, when we might not have 4 cards in the pile
        assert(hand.get_num_cards() == 4)

        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Are any of the cards in the hand a Jack? If so, does the suit of the Jack match the starter? Then list them.
        jacks_in_hand = []
        for i in range(len(cards)):
            if cards[i].pips == "J":
                if cards[i].suit == starter.suit:
                    jacks_in_hand.append(cards[i])

        # Since cribbage should always be played with a single, non-infinite deck, we should never find more than one Jack where the suit
        # matches the starter.

        assert (len(jacks_in_hand) <= 1)
                    
        if len(jacks_in_hand) == 1:
            info.number_instances = 1
            info.instance_list = [jacks_in_hand]
            info.score = info.number_instances * self._score_per_combo
        
        return info


class FifteenCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score 15's in a cribbage hand.
    """
    def __init__(self):
        """
        Construct the class for 15's scoring combination in cribbage hand.
        """
        self._combo_name = 'fifteen'
        self._score_per_combo = 2
        
    def score(self, hand = Hand(), starter = None):
        """
        Search hand for all fifteens, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The hand to search for fifteens, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the fifteens in the hand, CribbageComboInfo object
        """
        # This is a cribbage hand, so make sure it has 4 cards ... NO ... pile during play may be more or less than 4
        # assert(hand.get_num_cards() == 4)
        
        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Add the starter card to the list of cards in the hand
        if starter is not None: cards.append(starter)
        
        permutations = []
        for size in range(2,len(cards)+1):
            # Add to the list of permutations all permutations of size of cards in the hand.
            permutations.extend(self.permutations(size, cards))
                    
        # Iterate through the many permutations and determine how many of them add to fifteen
        for p in permutations:
            # Add up the cards in the permutation
            p_count = 0
            for c in p:
                p_count += c.count_card()
            if p_count == 15:
                info.number_instances += 1
                info.instance_list.append(p)
                
        # Set the score in the info object
        info.score = info.number_instances * self._score_per_combo      
        
        return info


class RunCombination(CribbageCombinationShowing):
    """
    Intended to search for, find, and score runs in a cribbage hand.
    """
    def __init__(self):
        """
        Construct the class for run scoring combination in cribbage hand.
        """
        self._combo_name = 'run'
        self._score_per_combo = 0 # Since scoring depends on length of run
        
    def score(self, hand = Hand(), starter = None):
        """
        Search hand for all runs, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The hand to search for runs, Hand object
        :parameter starter: The starter card, Card object
        :return: CribbageComboInfo object with information about the runs in the hand, CribbageComboInfo object
        """
        # This is a cribbage hand, so make sure it has 4 cards ... NO ... pile during play may be more or less than 4
        # assert(hand.get_num_cards() == 4)
        
        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        cards = hand.get_cards()

        # Add the starter card to the list of cards in the hand
        if starter is not None: cards.append(starter)
        
        # Must be a "greedy" algorithm, looking for long runs first

        run_found = False
        for size in range(5,2,-1): # The range is [5, 4, 3]
        
            # Create a list of all permutations of five cards in the hand.
            permutations = self.permutations(size, cards)

            # Do we have a run of size cards?
            # Iterate through the size-card permutations and determine how many of them are a run
            for p in permutations:
                is_run = True
                # Sort the cards in the permutation, this requires, Card class to have __lt__ method implemented
                p.sort()
                first_card = p.pop(0)
                prev_sequence_count = first_card._get_sequence_count()
                for c in p:
                    if c._get_sequence_count() == prev_sequence_count + 1:
                        prev_sequence_count = c._get_sequence_count()
                    else:
                        is_run = False
                        break
                if is_run:
                    run_found = True
                    info.number_instances += 1
                    info.score += size
                    # Since we popped the first card off p, when need to reassemble the original p to append it to the info.instance_list of lists
                    list_to_append = [first_card]
                    list_to_append.extend(p)
                    info.instance_list.append(list_to_append)

            # If we found one or more runs at the current size, then don't look for any more at the next lower size, because, of course
            # if we have a run at (size+1) we will also have one at (size), but it will be duplicative.
            # This is the algorithm being "greedy".
            if run_found: break
        
        return info

    
class PairCombinationPlaying(CribbageCombinationPlaying):
    """
    Intended to search for, find, and score pairs in a cribbage play pile.
    """
    def __init__(self):
        """
        Construct the class for pair scoring combination in cribbage play pile.
        """
        self._combo_name = 'pair'
        self._score_per_combo = 2
        
    def score(self, pile = Hand()):
        """
        Search pile for all "uninteruppted" pairs in the most recently played cards, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The play pile to search for pairs, Hand object
        :return: CribbageComboInfo object with information about the pairs in the play pile, CribbageComboInfo object
        """
        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        # Note that it is important that the if strucure here is "greedy" attempting to score the higher combinations first
        if (len(pile) >= 4) and (pile[-2].pips == pile[-1].pips) and (pile[-3].pips == pile[-2].pips) and (pile[-4].pips == pile[-3].pips):
                # Last card played made a double pair royal (4 of a kind)
                info.combo_name = 'double pair royal'
                info.number_instances = 1
                info.score = 12
                info.instance_list.append([pile[-4], pile[-3], pile[-2], pile[-1]])
        elif (len(pile) >= 3) and (pile[-2].pips == pile[-1].pips) and (pile[-3].pips == pile[-2].pips):
                # Last card played made a pair royal (3 of a kind)
                info.combo_name = 'pair royal'
                info.number_instances = 1
                info.score = 6
                info.instance_list.append([pile[-3], pile[-2], pile[-1]])
        elif (len(pile) >= 2) and (pile[-2].pips == pile[-1].pips):
                # Last card played made a pair royal (3 of a kind)
                info.combo_name = 'pair'
                info.number_instances = 1
                info.score = 2
                info.instance_list.append([pile[-2], pile[-1]])
        
        return info


class RunCombinationPlaying(CribbageCombinationPlaying):
    """
    Intended to search for, find, and score runs in a cribbage play pile.
    """
    def __init__(self):
        """
        Construct the class for run scoring combination in cribbage play pile.
        """
        self._combo_name = 'run'
        self._score_per_combo = 0 # Since scoring depends on length of run
        
    def score(self, pile = Hand()):
        """
        Search pile for all "uninteruppted" runs in the most recently played cards, tally up the score, and return a CribbageComboInfo object.
        :parameter hand: The play pile to search for runs, Hand object
        :return: CribbageComboInfo object with information about the runs in the play pile, CribbageComboInfo object
        """
        info = CribbageComboInfo()
        info.combo_name = self._combo_name

        run_size = 0
        
        # A run is a minimum of 3 cards and can't be more than 8 because each player only has 4 cards to play
        # This is a "greedy" algortihm, seeking to find the largest run first, and stopping there
        for x in range(len(pile),2,-1):
            if not self.test_last_x_cards_for_run(pile, x):
                continue
            else:
                run_size = x
                break
                
        if run_size > 0:
            info.number_instances = 1
            info.score = run_size
            the_run = [pile[i] for i in range(-1,(-run_size-1),-1)]
            the_run.sort()
            info.instance_list.append(the_run)
        
        return info

    def test_last_x_cards_for_run(self, pile = Hand(), x = 3):
        """
        Utility function called by score().
        :parameter pile: The pile of played cards to be examined for runs, Hand instance
        :parameter x: The number of cards backwards from the last card played to examine, int
        :return: True if last x cards in pile are a run, otherwise False, boolean
        """
        if len(pile) >= x:
            is_run = True
            # pile has at least x cards, so
            # form a list of the last x cards in pile
            cards = [pile[i] for i in range(-1,(-x-1),-1)]
            cards.sort()
            prev_sequence_count = cards.pop(0)._get_sequence_count()
            for c in cards:
                if c._get_sequence_count() == prev_sequence_count + 1:
                    prev_sequence_count = c._get_sequence_count()
                else:
                    is_run = False
                    break
        else:
            is_run = False
        return is_run


class FifteenCombinationPlaying(CribbageCombinationPlaying):
    """
    Intended to search for, find, and score 15's in a cribbage play pile.
    """
    def __init__(self):
        """
        Construct the class for fifteen scoring combination in cribbage play pile.
        """
        self._combo_name = 'fifteen'
        self._score_per_combo = 2
        
    def score(self, pile = Hand()):
        """
        Test if the pile of most recently played cards qualifies as a fifteen, tally up the score, and return a CribbageComboInfo object.
        Assumes that the pile contains only the played cards for the current go round so far, so that if the pile sums to fifteen, then, and only then
        will a fifteen be scored.
        :parameter hand: The play pile to test for a fifteen, Hand object
        :return: CribbageComboInfo object with information about the fifteen in the pile, CribbageComboInfo object
        """
        info = CribbageComboInfo()
        info.combo_name = self._combo_name
        
        pile_sum = 0
        for c in pile:
            pile_sum += c.count_card()

        if pile_sum == 15:
                info.number_instances = 1
                info.score = info.number_instances * self._score_per_combo
                info.instance_list.append(pile)

        return info
