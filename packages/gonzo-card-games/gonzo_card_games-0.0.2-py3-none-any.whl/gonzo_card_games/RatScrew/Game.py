from gonzo_card_games.Templates.CardGameTemplate import CardGameTemplate
from gonzo_card_games.CardDeck.CardDeck import CardDeck
from gonzo_card_games.RatScrew.RoundCardStack import RoundCardStack
from gonzo_card_games.RatScrew.Player import Player


class Game(CardGameTemplate):
    """
    Class to run and manage gameplay state of Rat Screw card game
    """

    _N_DECKS = 1
    _MAX_CARDS = _N_DECKS * 52
    _MAX_PLAYERS = _MAX_CARDS

    def __init__(self) -> None:
        """
        Initialize instance of Game
        """
        self._game_title = "Rat Screw"
        self.reset_game_parameters()

    def reset_game_parameters(self) -> None:
        """
        Resets game parameters to initial/empty states
        """
        # Parameters for tracking players
        self._play_keys = dict()
        self._slap_keys = dict()
        self._players = list()
        # Parameters for tracking game state
        self._round_stack = RoundCardStack()
        self._game_winner = None
        self._reset_round_parameters()

    def _reset_round_parameters(self) -> None:
        """
        Resets round parameters to initial states
        """
        self._round_stack.reset()
        self._round_winner = None
        self._won_by_slap = False
        self._player_turn_over = False

    @property
    def game_winner(self) -> int | None:
        """Return the index of the player who won the most recently completed game, or None if no winner yet."""
        return self._game_winner

    @game_winner.setter
    def game_winner(self, value) -> None:
        """Set game_winner to read-only"""
        raise AttributeError("game_winner is a read-only attribute")

    def print_rules(self) -> None:
        """
        Print rat screw game rules to screen
        """
        print("Rat Screw Game Rules:")
        print(
            "1. Objective of the game is to be the first player to collect all the cards. Each player starts with an equal number of cards in their stack."
        )
        print(
            "2. Each round players take turns playing cards from their stack to the center pile."
        )
        print(
            "3. If a face card is played, the next player must play another face card within a certain number of tries (Ace=4 tries, King=3 tries, Queen=2 tries, Jack=1 try).\n   If they fail, the previous player wins the round and adds the center pile to their stack."
        )
        print(
            "4. Players can slap the pile when certain conditions are met to win the pile instantly.\n   Conditions for slapping are if the last two cards match in value (i.e., double) or if the last card matches the card two before it in value (i.e., sandwich)."
        )
        print("5. Each round starts with the player that won the previous round.")
        print("6. The game continues until one player has all the cards.")
        print()

    def print_controls(self) -> None:
        """
        Print rat screw game controls to screen
        """
        print("Rat Screw Game Controls:")
        print(
            "1. At the start of the game each player chooses two unique action keys, a play key and a slap key."
        )
        print("2. At any point of a round players can input any of their action keys.")
        print(
            "3. Once players have inputted action keys, hit 'enter' to submit player actions for processing."
        )
        print(
            "4. A player's play key will only be processed if it's their turn to play and will only be processed once per action submission."
        )
        print(
            "5. The action keys for each player will be printed out at the start of each round, along with the current number of cards they have"
        )
        print(
            "6. At any given time the player whose turn it is will be indicated by the number next to the action input reciever (i.e., P#>) "
        )
        print()

    def play_game(self) -> None:
        """
        Play rat screw game
        """
        print("Starting new rat screw game")
        # Setup game for players
        self._setup_game()
        # Play rounds until there is a winner for the game
        self._round_winner = 0
        while self.game_winner is None:
            self._play_round(starting_player=self._round_winner)
            # check if someone won after round
            self._check_for_winner()
        print(f"Player #{self.game_winner+1} has won the game!")

    def _ask_user_for_number_of_players(self) -> int:
        """
        Ask user how many players will be part of game and validate input

        Returns
        -------
        Integer representing number of players requested
        """
        n_players = "dummy"
        while not n_players.isnumeric():
            n_players = input("How many players are part of this game? ")
        if int(n_players) > self._MAX_PLAYERS or int(n_players) < 2:
            print(f"Number of players must be between 2 and {self._MAX_PLAYERS}")
            return self._ask_user_for_number_of_players()
        return int(n_players)

    def _setup_game(self) -> None:
        """
        Setup rat screw game with n_players playing
        """
        # Ensure that game parameters are at defaults
        self.reset_game_parameters()
        # Get number of players for the game
        n_players = self._ask_user_for_number_of_players()
        print(f"{n_players} players are part of this game")
        # Create initial stack for each player
        fresh_deck = CardDeck(nDecks=self._N_DECKS)
        initial_card_stacks = fresh_deck.deal_deck(nPiles=n_players)
        # Move left over cards from fresh deck to round stack penalty stack
        while fresh_deck.nCards > 0:
            self._round_stack.add_penalty_card(fresh_deck.deal_card())
        # initialize each player with stack of cards and action keys assigned
        for p_idx, p_card_stack in enumerate(initial_card_stacks):
            print(f"Setting up player #{p_idx+1}")
            # intialize player
            p = Player(
                invalid_action_keys=(self._play_keys.keys() | self._slap_keys.keys())
            )
            # add action keys to dictionary to be able to reverse look up player index by their action keys
            self._play_keys[p.play_key] = p_idx
            self._slap_keys[p.slap_key] = p_idx
            # give player initial stack
            p.card_stack = p_card_stack
            # add player to game
            self._players.append(p)

    def _play_round(self, starting_player: int) -> None:
        """
        Play a single round of rat screw and update game state parameters

        Parameters
        ----------
        starting_player: int
            Index of player to start round
        """
        print("--- New Round Starting ---")
        # Show current card counts and controls for each player
        for p_idx, p in enumerate(self._players):
            print(
                f"Player #{p_idx+1} has {p.card_stack.nCards} cards. Play key: '{p.play_key}', Slap key: '{p.slap_key}'"
            )
        print(f"Player #{starting_player+1} goes first.")
        previous_player = None
        current_player = starting_player
        self._reset_round_parameters()
        while self._round_winner is None:
            # Check to see if current player's turn is over
            if self._player_turn_over:
                previous_player = current_player
                current_player = self._get_next_elgible_player(current_player)
                self._player_turn_over = False
                if current_player == previous_player:
                    # no other players have cards so current player wins the round (and game)
                    self._round_winner = current_player
                    break

            # await player action(s)
            player_actions = input(f"P#{current_player+1}> ")

            # Process player actions and update game state
            self._process_mid_round_actions(
                player_actions, current_player, previous_player
            )

        # Award round stack to round winner
        print(f"Player #{self._round_winner+1} has won the round!")
        if self._won_by_slap:
            self._players[self._round_winner].take_round_stack(self._round_stack)
        else:
            print("Use either action key to collect cards.")
            cards_collected = False
            while not cards_collected:
                player_actions = input(f"P#{self._round_winner+1}> ")
                cards_collected = self._process_round_end_actions(player_actions)

    def _check_for_winner(self) -> None:
        """
        Update game_winner state based on if any player has collected all cards
        """
        self._game_winner = None
        # Iterate through players to see if anyone has all the cards
        for p_idx, p in enumerate(self._players):
            if p.card_stack.nCards == self._MAX_CARDS:
                self._game_winner = p_idx
                return

    def _get_next_elgible_player(self, current_player_idx: int) -> int:
        """
        Get index of next player who has cards to play

        Parameters
        ----------
        current_player_idx: int
            Index of current player

        Returns
        ----------
        Index of next player with cards to play
        """
        n_players = len(self._players)
        next_player_idx = (current_player_idx + 1) % n_players
        while self._players[next_player_idx].card_stack.nCards == 0:
            next_player_idx = (next_player_idx + 1) % n_players
            if next_player_idx == current_player_idx:
                # No other players have cards
                break
        return next_player_idx

    def _process_mid_round_actions(
        self,
        player_actions: str,
        current_player_idx: int,
        previous_player_idx: int,
    ) -> None:
        """
        Update game state parameters based on player actions during an active round

        Parameters
        ----------
        player_actions: str
            String of player actions input
        current_player_idx: int
            Index of current player
        previous_player_idx: int
            Index of previous player
        """
        play_once_checker = set()
        # Iterate through player actions
        for key in player_actions:
            # Ensure each key is only processed once per turn
            if key in play_once_checker:
                continue
            play_once_checker.add(key)
            # Process action if key matches play or slap keys
            if (
                key == self._players[current_player_idx].play_key
                and not self._player_turn_over
            ):
                self._process_mid_round_playing_card(
                    current_player_idx, previous_player_idx
                )
                # Stop processing other player actions since card has been played
                break
            elif key in self._slap_keys:
                slapping_player_idx = self._slap_keys[key]
                self._process_mid_round_slapping(
                    slapping_player_idx, current_player_idx
                )
                if self._round_winner is not None:
                    break

    def _process_mid_round_playing_card(
        self, current_player_idx: int, previous_player_idx: int
    ) -> None:
        """
        Update game state parameters based on current player of active round playing card to round stack

        Parameters
        ----------
        current_player_idx: int
            Index of current player
        previous_player_idx: int
            Index of previous player
        """
        # Play a card from player's stack
        played_card = self._players[current_player_idx].play_card()
        self._round_stack.add_played_card(played_card)
        # Print card to screen
        print(played_card)
        # Determine if player's turn is over (satisfied current face card requirement)
        self._player_turn_over = (
            played_card.isFaceCard() or self._round_stack.need_face_card is False
        )
        # Check if round was been won
        if self._round_stack.has_stack_been_won() or (
            not self._player_turn_over
            and self._players[current_player_idx].card_stack.nCards < 1
        ):
            self._round_winner = previous_player_idx
            self._player_turn_over = True
        else:
            self._round_winner = None

    def _process_mid_round_slapping(
        self, slapping_player_idx: int, current_player_idx: int
    ) -> None:
        """
        Update game state parameters based on player slapping round stack during an active round

        Parameters
        ----------
        slapping_player_idx: int
            Index of player who slapped the stack
        current_player_idx: int
            Index of current player
        """
        # Check if slap is valid and round was won
        if self._round_stack.is_valid_slap():
            print(f"Player #{slapping_player_idx+1} made a valid slap!")
            self._round_winner = slapping_player_idx
            self._won_by_slap = True
            return
        # Process an invalid slap
        print(f"Player #{slapping_player_idx+1} made an invalid slap!")
        # If slapper has no cards, they cannot pay penalty
        if self._players[slapping_player_idx].card_stack.nCards < 1:
            return
        # Provide penalty card for invalid slap
        self._round_stack.add_penalty_card(
            self._players[slapping_player_idx].play_card()
        )
        # If currrent player check that they still have cards after penalty
        if slapping_player_idx == current_player_idx:
            self._player_turn_over = (
                self._players[current_player_idx].card_stack.nCards < 1
            )

    def _process_round_end_actions(self, player_actions: str) -> bool:
        """
        Update game state parameters based on actions at the end of round

        Parameters
        ----------
        player_actions: str
            String of player actions input

        Returns
        ----------
        Boolean indicating if round stack was collected by someone
        """
        stack_collected = False
        round_winner = self._players[self._round_winner]
        play_once_checker = set()
        # Iterate through player actions
        for key in player_actions:
            # Ensure each key is only processed once per turn
            if key in play_once_checker:
                continue
            play_once_checker.add(key)
            # Process round winner collecting round stack or other players slapping the stack
            if key == round_winner.play_key or key == round_winner.slap_key:
                # round winner collected round stack so stop processing
                stack_collected = True
                break
            elif key in self._slap_keys:
                # Process a slap
                slapping_player_idx = self._slap_keys[key]
                if self._round_stack.is_valid_slap():
                    # Stole round stack with a valid slap
                    print(f"Player #{slapping_player_idx+1} made a valid slap!")
                    self._round_winner = slapping_player_idx
                    self._won_by_slap = True
                    stack_collected = True
                    break
                else:
                    # Penality slap
                    print(f"Player #{slapping_player_idx+1} made an invalid slap!")
                    self._round_stack.add_penalty_card(
                        self._players[slapping_player_idx].play_card()
                    )
        # Give cards to round winner (either from pickup up cards or slapping stack)
        if stack_collected:
            self._players[self._round_winner].take_round_stack(self._round_stack)
            return True
        else:
            return False
