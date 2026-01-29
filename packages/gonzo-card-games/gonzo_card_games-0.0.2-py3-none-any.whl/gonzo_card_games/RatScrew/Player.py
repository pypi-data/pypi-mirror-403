from gonzo_card_games.CardDeck.CardDeck import CardDeck
from gonzo_card_games.CardDeck.Card import Card
from gonzo_card_games.RatScrew.RoundCardStack import RoundCardStack


class Player:
    """
    Manage player state of participant in game of rat screw
    """

    def __init__(self, invalid_action_keys: set = None) -> None:
        """
        Intialize Player instance and set desired keys for actions
        """
        if invalid_action_keys is None:
            invalid_action_keys = set()
        # play key (put card down)
        key_selection = input("Input key for playing cards by player: ")
        while not self._is_valid_action_key(key_selection, invalid_action_keys):
            print("Invalid action key, please try again")
            key_selection = input("Input key for playing cards by player: ")
        self._play_key = key_selection
        invalid_action_keys.add(key_selection)
        # slap key (slap card stack)
        key_selection = input("Input key for slapping card stack by player: ")
        while not self._is_valid_action_key(key_selection, invalid_action_keys):
            print("Invalid action key, please try again")
            key_selection = input("Input key for slapping card stack by player: ")
        self._slap_key = key_selection
        # player hand / card stack
        self.card_stack = CardDeck(nDecks=0)

    @property
    def play_key(self) -> str:
        """Return value of the key that player uses for playing cards"""
        return self._play_key

    @play_key.setter
    def play_key(self, value) -> None:
        """Set play_key to read-only"""
        raise AttributeError("Play key can only be set during initalization of player")

    @property
    def slap_key(self) -> str:
        """Return value of the key that player uses for slapping the card stack"""
        return self._slap_key

    @slap_key.setter
    def slap_key(self, value) -> None:
        """Set slap_key to read-only"""
        raise AttributeError("Slap key can only be set during initalization of player")

    @property
    def card_stack(self) -> CardDeck:
        """Return player's the players deck of cards"""
        return self._card_stack

    @card_stack.setter
    def card_stack(self, stack: CardDeck) -> None:
        """Ensure that card_stack is set as a deck of cards"""
        if not isinstance(stack, CardDeck):
            raise TypeError("Player card stack must be an instance of a CardDeck class")
        self._card_stack = stack

    def play_card(self) -> Card:
        """
        Play a card from player's card stack

        Returns
        -------
        Card to be played from the player's card stack
        """
        if self.card_stack.nCards < 1:
            raise IndexError("No cards left in player's card stack")
        return self.card_stack.deal_card()

    def take_round_stack(self, round_stack: RoundCardStack) -> None:
        """
        Remove cards from round stack and add it to player's card stack

        Parameters
        ----------
        round_stack: RoundCardStack
            The round stack that is being added to the player's card stack
        """
        if not isinstance(round_stack, RoundCardStack):
            raise TypeError(
                "Player can only add cards from a RoundCardStack instance to their card stack"
            )
        self.card_stack.combine_decks(round_stack.penalty_card_stack, onTop=False)
        self.card_stack.combine_decks(round_stack.played_card_stack, onTop=False)
        # Reset round stack
        round_stack.reset()

    @staticmethod
    def _is_valid_action_key(key: str, invalid_action_keys: set = None) -> bool:
        """
        Determine if key to use for player action is valid

        Parameters:
        -----------
        key: str,
            Character that player wants to use for one of their action keys
        invalid_action_keys: set, optional
            Set of action keys that should be seen as invalid options (default: None)

        Returns:
        -----------
        Boolean indicating whether key is a valid selection for an action key
        """
        if invalid_action_keys is None:
            invalid_action_keys = set()

        if key in invalid_action_keys:
            return False

        return len(key) == 1
