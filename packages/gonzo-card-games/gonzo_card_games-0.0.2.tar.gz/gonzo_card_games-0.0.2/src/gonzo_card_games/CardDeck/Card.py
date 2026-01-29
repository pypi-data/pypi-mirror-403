class Card:
    """
    A class representing a single playing card.
    """

    _valid_values = {
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "jack",
        "queen",
        "king",
        "ace",
    }

    _valid_suits = {"hearts", "diamonds", "clubs", "spades"}

    def __init__(self, value: str, suit: str) -> None:
        """
        Initializes a playing card with a value and suit.

        Parameters
        ----------
        value: str
            The value of the card (e.g., '2', '3', ..., '10', 'jack', 'queen', 'king', 'ace')
        suit: str
            The suit of the card (e.g., 'hearts', 'diamonds', 'clubs', 'spades')
        """
        self.value = value
        self.suit = suit

    @property
    def value(self) -> str:
        """
        Returns the value of the card.
        """
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        """
        Sets the value of the card.
        """
        if value.lower() not in self._valid_values:
            raise ValueError("Invalid card value")
        self._value = value.lower()

    @property
    def suit(self) -> str:
        """
        Returns the suit of the card.
        """
        return self._suit

    @suit.setter
    def suit(self, suit: str) -> None:
        """
        Sets the suit of the card.
        """
        if suit.lower() not in self._valid_suits:
            raise ValueError("Invalid card suit")
        self._suit = suit.lower()

    def sameSuit(self, card2: "Card") -> bool:
        """
        Checks if two Card objects have the same suit.

        Parameters
        ----------
        card2: Card
            The other Card object to compare with.

        Returns
        ----------
        Boolean indicating if both cards have the same suit.
        """
        return self.suit == card2.suit

    def sameValue(self, card2: "Card") -> bool:
        """
        Checks if two Card objects have the same value.

        Parameters
        ----------
        card2: Card
            The other Card object to compare with.

        Returns
        ----------
        Boolean indicating if both cards have the same value.
        """
        return self.value == card2.value

    def isFaceCard(self) -> bool:
        """
        Checks if the card is a face card (jack, queen, king, ace).

        Returns
        -----------
        Boolean indicating if the card is a face card or not.
        """
        return self.value in {"jack", "queen", "king", "ace"}

    def __eq__(self, card2: "Card") -> bool:
        """
        Checks if two Card objects are equal based on their value and suit.
        """
        if not isinstance(card2, Card):
            return False
        return (self.value == card2.value) and (self.suit == card2.suit)

    def __repr__(self) -> str:
        """
        Returns a string representation of the card.
        """
        return f"Card(value='{self.value}', suit='{self.suit}')"

    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the card.
        """
        return f"{self.value.capitalize()} of {self.suit.capitalize()}"
