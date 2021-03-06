''' Objects used in playing card games.
'''
import itertools
import random
from collections import namedtuple, Counter

Card = namedtuple('Card', ('rank', 'suit'))

RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')
SUITS = ('H', 'D', 'C', 'S')
POKER_HANDS = {
    'HIGH_CARD': 0,
    'PAIR': 1,
    'TWO_PAIR': 2,
    'THREE_KIND': 3,
    'STRAIGHT': 4,
    'FLUSH': 5,
    'FULL_HOUSE': 6,
    'FOUR_KIND': 7,
    'STRAIGHT_FLUSH': 8,
    'ROYAL_FLUSH': 9,
}


class Deck(object):
    ''' Deck(s) of cards. '''

    def __init__(self, num_decks=1):
        self.deck = self._create_cards(num_decks)
        self.shuffle()
        self._idx = 0

    def _create_cards(self, num_decks):
        card_suit_combos = itertools.product(RANKS * num_decks, SUITS)
        return list(Card(rank, suit) for rank, suit in card_suit_combos)

    def __len__(self):
        return len(self.deck)

    def shuffle(self):
        ''' Shuffle the deck of cards in place. '''
        random.shuffle(self.deck)

    def deal(self, num_cards=1):
        ''' Return num_cards of cards from the deck. '''
        if self.cards_remaining > num_cards:
            dealt = list(itertools.islice(self.deck,
                                          self._idx, self._idx + num_cards))
            self._idx += num_cards
            return dealt
        else:
            raise ValueError('Not enough cards remaining.')

    @property
    def cards_remaining(self):
        ''' The number of cards yet to be dealt. '''
        return len(self.deck) - self._idx


class BlackJackHand(object):
    ''' A single hand of blackjack. '''

    CARD_VALUES = dict(
        zip(
            RANKS,
            (*range(2, 11), 10, 10, 10, 11)  # 2-10, J, Q, K, A
        )
    )

    def __init__(self, cards):
        self.cards = cards

    def __lt__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

    def __le__(self, other):
        return self.score <= other.score

    def __ge__(self, other):
        return self.score >= other.score

    @property
    def score(self):
        ''' The numerical value of the hand. '''
        hand_score = 0
        for card in self.cards:
            if 'A' in card:
                card_score = self._handle_ace(hand_score)
            else:
                card_score = self.CARD_VALUES[card.rank]
            hand_score += card_score
        return hand_score

    def _handle_ace(self, current_hand_score):
        if current_hand_score > 10:
            return 1
        else:
            return 11


class PokerHand(object):

    def __init__(self, cards):
        self.cards = cards
        self.hand_order = (
            # order of checks in hand determination
            'royal_flush',
            'four_kind',
            'straight_flush',
            'full_house',
            'flush',
            'straight',
            'three_kind',
            'two_pair',
            'pair',
            'high_card',
        )

    def __lt__(self, other):
        return self.hand_rank > other.hand_rank

    def __gt__(self, other):
        return self.hand_rank < other.hand_rank

    def __le__(self, other):
        return self.hand_rank >= other.hand_rank

    def __ge__(self, other):
        return self.hand_rank <= other.hand_rank

    @property
    def hand_rank(self):
        # Returns the best (lowest) hand rank the cards in self.cards can make.
        hand = next(
            hand for hand in self.hand_order
            if getattr(self, 'is_' + hand)
        )
        return self.hand_order.index(hand)

    @property
    def suits(self):
        return [x.suit for x in self.cards]

    @property
    def ranks(self):
        return [x.rank for x in self.cards]

    @property
    def is_high_card(self):
        return (not self.is_straight) \
            and (not self.is_flush) \
            and (len(set(self.ranks)) == 5)

    @property
    def is_pair(self):
        return 2 in Counter(self.ranks).values()

    @property
    def is_two_pair(self):
        return 2 in Counter(Counter(self.ranks).values()).values()

    @property
    def is_three_kind(self):
        return 3 in Counter(self.ranks).values()

    @property
    def is_straight(self):
        if 'A' in self.ranks:
            # special case starting with Ace.  Only one possible sorted char
            # order.
            return sorted(self.ranks) == ['2', '3', '4', '5', 'A']
        else:
            rank_indices = [RANKS.index(x) for x in self.ranks]
            sub_length = max(rank_indices) - min(rank_indices)
            return self._all_unique_ranks() and sub_length == 4

    @property
    def is_flush(self):
        return len({*self.suits}) == 1 and len(self.cards) == 5

    @property
    def is_full_house(self):
        return self.is_pair and self.is_three_kind

    @property
    def is_four_kind(self):
        return 4 in Counter(self.ranks).values()

    @property
    def is_straight_flush(self):
        return self.is_straight and self.is_flush

    @property
    def is_royal_flush(self):
        # only one possible sorted char order of a royal flush
        return sorted(self.ranks) == ['10', 'A', 'J', 'K', 'Q'] \
            and self.is_flush

    def _all_unique_ranks(self):
        return len({*self.ranks}) == 5


class HoldEmHand(PokerHand):

    def __init__(self, cards, community_cards):
        super(HoldEmHand, self).__init__(cards)
        self.community_cards = community_cards

    @property
    def hand_rank(self):
        '''
        Make the best hand using the 2 cards held plus the 0 or 3 to 5
        community cards.
        '''
        if self.community_cards:
            best_rank = 1e6  # sentinel value
            for card_combo in itertools.combinations(self.community_cards, 3):
                cards = self.cards + list(card_combo)
                current_rank = PokerHand(cards).hand_rank
                best_rank = current_rank if current_rank < best_rank else best_rank
            return best_rank
        else:
            return PokerHand(self.cards).hand_rank
