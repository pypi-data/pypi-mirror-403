from gonzo_card_games.CardDeck.CardDeck import CardDeck
from gonzo_card_games.CardDeck.Card import Card


class RoundCardStack:
    """
    Class to manage the stack of cards played during a round of Rat Screw
    """

    def __init__(self) -> None:
        """Initialize instance of RoundCardStack"""
        self.reset()

    def reset(self) -> None:
        """Reset round stack to intialized state"""
        self._played_card_stack = CardDeck(nDecks=0)
        self._penalty_card_stack = CardDeck(nDecks=0)
        self._need_face_card = False
        self._face_card_countdown = 0

    @property
    def need_face_card(self) -> bool:
        """Return round stack state of needing a face card added to it"""
        return self._need_face_card

    @need_face_card.setter
    def need_face_card(self, value) -> None:
        """Set need_face_card to read-only"""
        raise AttributeError("need_face_card is a read-only attribute")

    @property
    def played_card_stack(self) -> CardDeck:
        """Return stack of cards that have been played to round stack"""
        return self._played_card_stack

    @played_card_stack.setter
    def played_card_stack(self, value) -> None:
        """Set played_card_stack to read-only"""
        raise AttributeError("played_card_stack is a read-only attribute")

    @property
    def penalty_card_stack(self) -> CardDeck:
        """Return stack of cards that have been added to the penalty pile"""
        return self._penalty_card_stack

    @penalty_card_stack.setter
    def penalty_card_stack(self, value) -> None:
        """Set penalty_card_stack to read-only"""
        raise AttributeError("penalty_card_stack is a read-only attribute")

    def _process_face_card(self, face_card: Card) -> None:
        """
        Update stack state based on the face card added

        Parameters
        ----------
        face_card: Card
            Face card that has been added to the round stack
        """
        # Check that card is a face card
        face_card_countdown_cypher = {"jack": 1, "queen": 2, "king": 3, "ace": 4}
        if face_card.value not in face_card_countdown_cypher:
            raise ValueError("Cannot process non face card as a face card")
        # Update stack state to indicate another facecard is needed and set a countdown
        self._need_face_card = True
        self._face_card_countdown = face_card_countdown_cypher[face_card.value]

    def add_played_card(self, card: Card) -> None:
        """
        Play a card onto the round stack and update face card countdown if necessary

        Parameters
        ----------
        card: Card
            The card to be played onto the round stack.
        """
        if not isinstance(card, Card):
            raise TypeError("Only Card instances can be added to the round stack")
        self.played_card_stack.add_card(card)
        # Check if played card is a face card
        if card.isFaceCard():
            self._process_face_card(card)
        else:
            self._face_card_countdown -= 1

    def add_penalty_card(self, card: Card) -> None:
        """
        Add penalty cards to the penalty stack

        Parameters
        ----------
        card: Card
            Card to be added to the penalty stack.
        """
        if not isinstance(card, Card):
            raise TypeError("Only Card instances can be added to the round stack")
        self.penalty_card_stack.add_card(card)

    def has_stack_been_won(self) -> bool:
        """
        Determine if stack has been won by a player

        Returns
        -------
        Boolean indicating whether the stack has been won
        """
        if self.need_face_card is False:
            return False
        return self._face_card_countdown < 1

    def is_valid_slap(self) -> bool:
        """
        Determine if slapping current stack is valid

        Returns
        -------
        Boolean indicating whether the stack is in a valid slap state
        """
        n_cards = self.played_card_stack.nCards
        if n_cards < 2:
            return False
        top_card = self.played_card_stack.see_card(0)
        second_card = self.played_card_stack.see_card(1)
        # Check for double
        if top_card.sameValue(second_card):
            return True
        # Check for sandwich
        if n_cards >= 3:
            third_card = self.played_card_stack.see_card(2)
            return top_card.sameValue(third_card)
        return False
