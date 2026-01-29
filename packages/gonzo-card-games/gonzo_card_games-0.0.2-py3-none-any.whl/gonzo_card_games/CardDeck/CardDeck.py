import random
from gonzo_card_games.CardDeck.Card import Card


class CardDeck:
    """
    A class representing a card deck containing one or more sets of standard 52 playing cards.
    """

    def __init__(self, nDecks: int = 1) -> None:
        """
        Initializes a standard card deck composed of one or more sets of 52 playing cards.

        Parameters
        ----------
        nDecks: int, optional
            The number of decks to include (default: 1)
        """
        self._cards = []
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        values = [
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "Jack",
            "Queen",
            "King",
            "Ace",
        ]
        for _ in range(nDecks):
            for suit in suits:
                for value in values:
                    self.add_card(Card(value, suit), onTop=True)
        self.shuffle()

    def shuffle(self) -> None:
        """
        Shuffles the deck of cards.
        """
        random.shuffle(self._cards)

    def deal_card(self, fromBottom=False) -> Card:
        """
        Deals a single card from the deck.

        Parameters
        ----------
        fromBottom: bool, optional
            If True, deals the card from the bottom of the deck; otherwise, deals from the top (default: False)

        Returns
        ----------
        Card object if available.
        """
        if len(self._cards) == 0:
            raise IndexError("No cards left in the deck")
        if fromBottom:
            return self._cards.pop(0)
        else:
            return self._cards.pop()

    def add_card(self, card: Card, onTop=False) -> None:
        """
        Adds a card into the deck.

        Parameters
        ----------
        card: Card
            The card to be added back to the deck.
        onTop: bool, optional
            If True, adds the card to the top of the deck; otherwise, adds it to the bottom (default: False)
        """
        if isinstance(card, Card) is False:
            raise TypeError("Only Card instances can be added to the deck")
        if onTop:
            self._cards.append(card)
        else:
            self._cards.insert(0, card)

    def pull_card(self, index: int) -> Card:
        """
        Pulls a card at the specified index out of the deck.

        Parameters
        ----------
        index: int
            The index of the card to retrieve.

        Returns
        ----------
        Card object at the specified index.
        """
        if index < 0 or index >= len(self._cards):
            raise IndexError("Card index out of range")
        return self._cards.pop(index)

    def insert_card(self, card: Card, index: int) -> None:
        """
        Inserts a card at the specified index in the deck.

        Parameters
        ----------
        card: Card
            The card to be inserted.
        index: int
            The index at which to insert the card.
        """
        if isinstance(card, Card) is False:
            raise TypeError("Only Card instances can be added to the deck")
        if index < 0 or index > len(self._cards):
            raise IndexError("Card index out of range")
        self._cards.insert(index, card)

    def see_card(self, index: int) -> Card:
        """
        Returns copy of card at the specified index of the deck.

        Parameters
        ----------
        index: int
            The index of the card to view.

        Returns
        ----------
        Copy of card object at the specified index.
        """
        if index < 0 or index >= len(self._cards):
            raise IndexError("Card index out of range")
        return Card(self._cards[index].value, self._cards[index].suit)

    def combine_decks(self, other_deck: "CardDeck", onTop=False) -> None:
        """
        Adds another CardDeck to the current deck.

        Parameters
        ----------
        other_deck: CardDeck
            The CardDeck to be added to the current deck.
        onTop: bool, optional
            If True, adds the other deck on top of the current deck; otherwise, adds it to the bottom (default: False)
        """
        if isinstance(other_deck, CardDeck) is False:
            raise TypeError("Only CardDeck instances can be added to the deck")
        if onTop:
            self._cards = self._cards + other_deck._cards
        else:
            self._cards = other_deck._cards + self._cards

    def deal_deck(self, nPiles: int) -> list["CardDeck"]:
        """
        Deals the as much of the deck as possible into specified number of piles.

        Parameters
        ----------
        nPiles: int
            The number of piles to deal the deck into.

        Returns
        ----------
        A list of CardDeck objects, each containing an equal number of cards.
        """
        self.shuffle()
        piles = [CardDeck(nDecks=0) for _ in range(nPiles)]
        leftover = len(self._cards) % nPiles
        while len(self._cards) > leftover:
            for pile in piles:
                pile.add_card(self.deal_card(), onTop=True)
        return piles

    @property
    def nCards(self) -> int:
        """
        Returns the current number of cards in the deck.
        """
        return len(self._cards)

    @property
    def cards(self) -> list[Card]:
        """
        Returns the list of cards in the deck.
        """
        # return copy of list of cards
        return self._cards[:]

    @cards.setter
    def cards(self, cards: list[Card]) -> None:
        """
        Sets the list of cards in the deck.
        """
        if isinstance(cards, list) is False:
            raise TypeError("cards must be a list of Card instances")
        for card in cards:
            self.add_card(card, onTop=True)

    def __repr__(self) -> str:
        """
        Returns a string representation of the CardDeck.
        """
        return f"CardDeck(nCards={self.nCards})"

    def __str__(self) -> str:
        """
        Returns a detailed string representation of the CardDeck.
        """
        card_list = ", ".join([card.__str__() for card in self._cards])
        return f"CardDeck with {self.nCards} cards: [{card_list}]"
