import pytest
from gonzo_card_games.CardDeck import CardDeck, Card
from gonzo_card_games.RatScrew import Game, RoundCardStack


class MockGame(Game):
    """
    Mock class of Game so that play_game method can be tested
    """

    def _play_round(self, starting_player):
        """
        Do nothing
        """
        pass

    def _check_for_winner(self):
        """
        Instantly assign winner for game
        """
        self._game_winner = len(self._players) - 1


class TestGame:
    """
    Test functionality of Game class.
    """

    def test_reset_game_parameters(self):
        """
        Test reset_game_parameters method of Game.
        """
        game = Game()
        # Modify game parameters to be set to something other than their default to ensure reset works
        game._play_keys = None
        game._slap_keys = None
        game._players = None
        game._round_stack = None
        game._game_winner = 1
        game._round_winner = 1
        game._won_by_slap = True
        game._player_turn_over = True

        # Reset game parameters
        game.reset_game_parameters()

        # Check that game parameters are reset to initial states
        assert game._play_keys == dict() and isinstance(game._play_keys, dict)
        assert game._slap_keys == dict() and isinstance(game._slap_keys, dict)
        assert game._players == list() and isinstance(game._players, list)
        assert isinstance(game._round_stack, RoundCardStack)
        assert game._round_stack.played_card_stack.nCards == 0
        assert game._round_stack.penalty_card_stack.nCards == 0
        assert game._round_stack.need_face_card is False
        assert game._round_stack._face_card_countdown == 0
        assert game._game_winner is None
        assert game._round_winner is None
        assert not game._won_by_slap
        assert not game._player_turn_over

    def test_reset_round_parameters(self):
        """
        Test reset_round_parameters method of Game.
        """
        game = Game()
        # Modify round parameters to be set to something other than their default to ensure reset works
        game._round_stack.add_played_card(Card("4", "hearts"))
        game._round_winner = 1
        game._won_by_slap = True
        game._player_turn_over = True

        # Reset game parameters
        game._reset_round_parameters()

        # Check that game parameters are reset to initial states
        assert game._round_stack.played_card_stack.nCards == 0
        assert game._round_stack.penalty_card_stack.nCards == 0
        assert game._round_stack.need_face_card is False
        assert game._round_stack._face_card_countdown == 0
        assert game._round_winner is None
        assert not game._won_by_slap
        assert not game._player_turn_over

    def test_game_winner(self):
        """
        Test game_winner attribute property and setter
        """
        game = Game()
        random_val = 5
        game._game_winner = random_val
        assert game.game_winner == random_val
        with pytest.raises(AttributeError):
            game.game_winner = random_val

    def test_print_rules(self):
        """
        Provide test coverage for print_rules method of Game
        """
        Game().print_rules()

    def test_print_controls(self):
        """
        Provide test coverage for print_controls method of Game
        """
        Game().print_controls()

    def test_ask_user_for_number_of_players_valid(self, monkeypatch):
        """
        Test _ask_user_for_number_of_players method of Game.
        """
        game = Game()

        # sequence of user inputs: invalid input followed by valid input
        user_inputs = ["3"]
        inputs = iter(user_inputs)

        # Patch the built-in 'input' function to use the iterator
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        n_players = game._ask_user_for_number_of_players()
        assert n_players == 3

    def test_ask_user_for_number_of_players_invalid(self, monkeypatch):
        """
        Test _ask_user_for_number_of_players method of Game when too many or too few players are provided.
        """
        game = Game()

        # sequence of user inputs: input non pos integer, input too many players, input too few players, input valid number of player
        user_inputs = ["foo", str(game._MAX_PLAYERS + 1), "1", "2"]
        inputs = iter(user_inputs)

        # Patch the built-in 'input' function to use the iterator
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        n_players = game._ask_user_for_number_of_players()
        assert n_players == 2

    def test_setup_game_with_valid_number_of_players(self, monkeypatch):
        """
        Test _setup_game method of Game with a valid number of players.
        """
        game = Game()
        n_players = 3
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d", "e", "f"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Check that the correct number of players have been added
        assert len(game._players) == n_players

        # Check that play and slap key dictionaries point to the correct player index
        for p_idx, player in enumerate(game._players):
            assert game._play_keys[player.play_key] == p_idx
            assert game._slap_keys[player.slap_key] == p_idx

        # Check that the card stack has been distributed among players
        total_player_cards = sum(player.card_stack.nCards for player in game._players)
        assert (
            total_player_cards
            + game._round_stack.played_card_stack.nCards
            + game._round_stack.penalty_card_stack.nCards
            == game._MAX_CARDS
        )

    def test_check_for_winner(self, monkeypatch):
        """
        Test _check_for_winner method of Game.
        """
        game = Game()
        n_players = 3
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d", "e", "f"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Initially, there should be no winner
        game._check_for_winner()
        assert game.game_winner is None

        # Give all cards to player 0 and check for winner
        winner_player_idx = 0
        for p_idx in range(n_players):
            if p_idx == winner_player_idx:
                game._players[p_idx].card_stack = CardDeck(nDecks=1)
            else:
                game._players[p_idx].card_stack = CardDeck(nDecks=0)

        # Run test and ensure that game state is updated as expected
        game._check_for_winner()
        assert game.game_winner == winner_player_idx

    def test_play_game(self, monkeypatch):
        """
        Provide test coverage for play_game method of Game
        """
        # Use mock class so that play_game loop only runs a single time for the sake of test coverage
        game = MockGame()
        # Patch the built-in 'input' function to provide unique keys for each player and number of players
        user_inputs = iter(
            [
                "2",  # number of players
                "a",  # player 1 play key
                "b",  # player 1 slap key
                "c",  # player 2 play key
                "d",  # player 2 slap key
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        # Run play_game method to provide test coverage
        game.play_game()

    def test_play_round(self, monkeypatch):
        """
        Test _play_round method of Game.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup cards for players so that can test round play
        starting_player = 0
        winning_player = 1
        game._players[starting_player].card_stack = CardDeck(nDecks=0)
        game._players[starting_player].card_stack.add_card(Card("3", "hearts"))
        game._players[starting_player].card_stack.add_card(Card("10", "diamonds"))
        game._players[winning_player].card_stack = CardDeck(nDecks=0)
        game._players[winning_player].card_stack.add_card(Card("jack", "spades"))

        # Patch the built-in 'input' function to force a sequence of plays
        user_inputs = iter(["a", "c", "a", "c"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        # Play round where second player loses since they cannot play a face card
        game._play_round(starting_player)
        assert game._round_winner == winning_player
        assert game._players[winning_player].card_stack.nCards == 3
        assert game._players[starting_player].card_stack.nCards == 0
        assert game._round_stack.played_card_stack.nCards == 0
        assert game._round_stack.penalty_card_stack.nCards == 0

    def test_play_round_game_winner(self, monkeypatch):
        """
        Test _play_round method of Game when a player wins the game which forces the round to end.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup cards for players so that can test round play
        starting_player = 0
        losing_player = 1
        game._players[starting_player].card_stack = CardDeck(nDecks=0)
        game._players[starting_player].card_stack.add_card(Card("3", "hearts"))
        game._players[starting_player].card_stack.add_card(Card("10", "diamonds"))
        game._players[losing_player].card_stack = CardDeck(nDecks=0)
        game._players[losing_player].card_stack.add_card(Card("7", "spades"))

        # Patch the built-in 'input' function to force a sequence of plays
        user_inputs = iter(["a", "c", "a", "a"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        # Play round where second player loses since they cannot play a face card
        game._play_round(starting_player)
        assert game._round_winner == starting_player

    def test_play_round_slap(self, monkeypatch):
        """
        Test _play_round method of Game when a player wins the round by slapping the stack.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup cards for players so that can test round play
        starting_player = 0
        winning_player = 1
        game._players[starting_player].card_stack = CardDeck(nDecks=0)
        game._players[starting_player].card_stack.add_card(Card("7", "hearts"))
        game._players[starting_player].card_stack.add_card(Card("ace", "diamonds"))
        game._players[winning_player].card_stack = CardDeck(nDecks=0)
        game._players[winning_player].card_stack.add_card(Card("7", "spades"))

        # Patch the built-in 'input' function to force a sequence of plays
        user_inputs = iter(["a", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        # Play round where second player loses since they cannot play a face card
        game._play_round(starting_player)
        assert game._round_winner == winning_player

    def test_get_next_elgible_player(self, monkeypatch):
        """
        Test _get_next_elgible_player method of Game.
        """
        game = Game()
        n_players = 4
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d", "e", "f", "g", "h"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Set players 1 and 2 to have no cards
        game._players[1].card_stack = CardDeck(nDecks=0)
        game._players[2].card_stack = CardDeck(nDecks=0)

        # Starting from player 0, the next elgible player should be player 3
        next_player = game._get_next_elgible_player(current_player_idx=0)
        assert next_player == 3

        # Starting from player 3, the next elgible player should be player 0
        next_player = game._get_next_elgible_player(3)
        assert next_player == 0

    def test_get_next_elgible_player_all_players_out(self, monkeypatch):
        """
        Test _get_next_elgible_player method of Game when all players have no cards.
        """
        game = Game()
        n_players = 4
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d", "e", "f", "g", "h"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Set all players to have no cards
        for p in game._players:
            p.card_stack = CardDeck(nDecks=0)

        # Since no one has cards, the next elgible player should be the current player
        for idx in range(n_players):
            next_player = game._get_next_elgible_player(current_player_idx=idx)
            assert next_player == idx

    def test_process_mid_round_playing_card_lost_round(self, monkeypatch):
        """
        Test _process_mid_round_playing_card method of Game when the player loses the round.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to require a face card to be played
        game._round_stack._need_face_card = True
        game._round_stack._face_card_countdown = 1

        # Override current player's card stack to have no face cards
        current_player_idx = 0
        game._players[current_player_idx].card_stack = CardDeck(nDecks=0)
        game._players[current_player_idx].card_stack.add_card(Card("2", "hearts"))

        # Test playing a card
        previous_player_idx = 1
        game._process_mid_round_playing_card(
            current_player_idx=current_player_idx,
            previous_player_idx=previous_player_idx,
        )
        assert game._round_winner == previous_player_idx
        assert game._player_turn_over is True

    def test_process_mid_round_playing_card_face_card_played(self, monkeypatch):
        """
        Test _process_mid_round_playing_card method of Game when a face card is played.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to not require a face card to be played
        game._round_stack._need_face_card = False
        game._round_stack._face_card_countdown = 0

        # Override current player's card stack to have a face card
        current_player_idx = 0
        game._players[current_player_idx].card_stack = CardDeck(nDecks=0)
        game._players[current_player_idx].card_stack.add_card(Card("king", "hearts"))

        # Test playing a card
        previous_player_idx = 1
        game._process_mid_round_playing_card(
            current_player_idx=current_player_idx,
            previous_player_idx=previous_player_idx,
        )
        assert game._round_winner is None  # no one should win the round
        assert game._player_turn_over is True  # since they played a face card

    def test_process_mid_round_playing_card_turn_still_going(self, monkeypatch):
        """
        Test _process_mid_round_playing_card method of Game when the current player can continue playing.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to require a face card to be played within two plays
        game._round_stack._need_face_card = True
        game._round_stack._face_card_countdown = 2

        # Override current player's card stack to have only one card
        current_player_idx = 0
        game._players[current_player_idx].card_stack = CardDeck(nDecks=0)
        game._players[current_player_idx].card_stack.add_card(Card("5", "hearts"))
        game._players[current_player_idx].card_stack.add_card(Card("9", "spades"))

        # Test playing a card
        previous_player_idx = 1
        game._process_mid_round_playing_card(
            current_player_idx=current_player_idx,
            previous_player_idx=previous_player_idx,
        )
        assert game._round_winner is None  # player can still play
        assert game._player_turn_over is False  # since countdown has not reached zero

    def test_process_mid_round_slapping_valid_slap(self, monkeypatch):
        """
        Test _process_mid_round_slapping method of Game when it's a valid slap.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in a valid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("5", "spades"))

        # Test slapping the stack
        slapping_player_idx = 0
        current_player_idx = 1
        game._process_mid_round_slapping(
            slapping_player_idx=slapping_player_idx,
            current_player_idx=current_player_idx,
        )
        assert game._round_winner == slapping_player_idx

    def test_process_mid_round_slapping_invalid_slap_no_cards(self, monkeypatch):
        """
        Test _process_mid_round_slapping method of Game when an invalid slap is done by a player with no cards.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in an invalid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("6", "spades"))

        # Set slapping player to have no cards
        slapping_player_idx = 0
        game._players[slapping_player_idx].card_stack = CardDeck(nDecks=0)

        # Test slapping the stack
        current_player_idx = 1
        game._process_mid_round_slapping(
            slapping_player_idx=slapping_player_idx,
            current_player_idx=current_player_idx,
        )
        assert game._round_winner is None

    def test_process_mid_round_slapping_invalid_slap_with_cards(self, monkeypatch):
        """
        Test _process_mid_round_slapping method of Game when an invalid slap is done by a player with cards.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in an invalid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("6", "spades"))

        # Ensure slapping player has cards
        slapping_player_idx = 0
        game._players[slapping_player_idx].card_stack = CardDeck(nDecks=0)
        game._players[slapping_player_idx].card_stack.add_card(Card("9", "clubs"))
        expected_cards_after_penalty = (
            game._players[slapping_player_idx].card_stack.nCards - 1
        )

        # Test slapping the stack
        current_player_idx = 1
        game._process_mid_round_slapping(
            slapping_player_idx=slapping_player_idx,
            current_player_idx=current_player_idx,
        )
        assert (
            game._players[slapping_player_idx].card_stack.nCards
            == expected_cards_after_penalty
        )

    def test_process_mid_round_slapping_invalid_slap_by_current_player(
        self, monkeypatch
    ):
        """
        Test _process_mid_round_slapping method of Game when an invalid slap is done by the current player.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in a invalid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("7", "spades"))

        # set current player to only have one card so they will have no cards after penalty
        slapping_player_idx = 0
        game._players[slapping_player_idx].card_stack = CardDeck(nDecks=0)
        game._players[slapping_player_idx].card_stack.add_card(Card("9", "clubs"))

        # Test slapping the stack by the current player
        game._process_mid_round_slapping(
            slapping_player_idx=slapping_player_idx,
            current_player_idx=slapping_player_idx,
        )
        assert game._player_turn_over is True

    def test_process_mid_round_actions_card_played(self, monkeypatch):
        """
        Test _process_mid_round_actions method of Game when a card is played.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        play_card_key = "a"
        user_inputs = iter([str(n_players), play_card_key, "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup player cards with a single known card
        current_player_idx = 0
        game._players[current_player_idx].card_stack = CardDeck(nDecks=0)
        played_card = Card("5", "hearts")
        game._players[current_player_idx].card_stack.add_card(played_card)

        # Test processing player actions
        previous_player_idx = 1
        game._process_mid_round_actions(
            player_actions=play_card_key,
            current_player_idx=current_player_idx,
            previous_player_idx=previous_player_idx,
        )
        assert game._round_winner is None
        assert game._player_turn_over is True
        assert game._players[current_player_idx].card_stack.nCards == 0
        assert game._round_stack.played_card_stack.nCards == 1
        assert game._round_stack.penalty_card_stack.nCards == 0
        assert game._round_stack.played_card_stack.see_card(0) == played_card

    def test_process_mid_round_actions_stack_slapped_multiple_attempts(
        self, monkeypatch
    ):
        """
        Test _process_mid_round_actions method of Game when attempted to be slapped multiple times by one person.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        slap_key = "b"
        user_inputs = iter([str(n_players), "a", slap_key, "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in a invalid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("6", "spades"))

        # Get expected number of cards after penalty
        slapping_player_idx = 0
        expected_cards_after_penalty = (
            game._players[slapping_player_idx].card_stack.nCards - 1
        )

        # Test slapping the stack
        current_player_idx = 1
        game._process_mid_round_actions(
            player_actions=slap_key * 3,  # multiple slap attempts
            current_player_idx=current_player_idx,
            previous_player_idx=0,
        )
        assert game._round_winner is None
        assert game._player_turn_over is False
        assert (
            game._players[slapping_player_idx].card_stack.nCards
            == expected_cards_after_penalty
        )
        assert game._round_stack.played_card_stack.nCards == 2
        assert game._round_stack.penalty_card_stack.nCards == 1

    def test_process_mid_round_actions_stack_slapped_successfully(self, monkeypatch):
        """
        Test _process_mid_round_actions method of Game when the stack is slapped successfully and won.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        slap_key = "b"
        user_inputs = iter([str(n_players), "a", slap_key, "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup round stack to be in a valid slap state
        game._round_stack.played_card_stack.add_card(Card("5", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("5", "spades"))

        # Test slapping the stack
        slapping_player_idx = 0
        current_player_idx = 1
        game._process_mid_round_actions(
            player_actions=slap_key,
            current_player_idx=current_player_idx,
            previous_player_idx=0,
        )
        assert game._round_winner == slapping_player_idx

    def test_process_mid_round_actions_no_valid_actions(self, monkeypatch):
        """
        Test _process_mid_round_actions method of Game when no valid actions are provided.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Test processing player actions with no valid actions
        current_player_idx = 0
        previous_player_idx = 1
        game._process_mid_round_actions(
            player_actions="xzy",  # invalid actions
            current_player_idx=current_player_idx,
            previous_player_idx=previous_player_idx,
        )
        assert game._round_winner is None
        assert game._player_turn_over is False

    def test_process_round_end_actions(self, monkeypatch):
        """
        Test _process_round_end_actions method of Game.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        play_card_key = "a"
        user_inputs = iter([str(n_players), play_card_key, "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup winner to have no cards
        winner_idx = 0
        game._players[winner_idx].card_stack = CardDeck(nDecks=0)

        # Setup round stack that was just won
        game._round_stack.played_card_stack.add_card(Card("jack", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("6", "spades"))

        # Test processing player actions
        game._round_winner = winner_idx
        cardpick_status = game._process_round_end_actions(play_card_key)
        assert cardpick_status
        assert game._players[winner_idx].card_stack.nCards == 2

    def test_process_round_end_actions_penality_slaps_only(self, monkeypatch):
        """
        Test _process_round_end_actions method of Game when only penality slaps are done and cards are not picked up.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        penality_slap_key = "d"
        user_inputs = iter([str(n_players), "a", "b", "c", penality_slap_key])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup winner to have no cards
        winner_idx = 0
        game._players[winner_idx].card_stack = CardDeck(nDecks=0)

        # Setup round stack that cannot be slapped
        game._round_stack.played_card_stack.add_card(Card("jack", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("6", "spades"))

        # Test processing player actions
        game._round_winner = winner_idx
        cardpick_status = game._process_round_end_actions(penality_slap_key)
        assert not cardpick_status
        assert game._players[winner_idx].card_stack.nCards == 0
        assert game._round_stack.penalty_card_stack.nCards == 1

    def test_process_round_end_actions_random_keys(self, monkeypatch):
        """
        Test _process_round_end_actions method of Game when series of random keys are inputted.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        user_inputs = iter([str(n_players), "a", "b", "c", "d"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Test processing player actions
        game._round_winner = 0
        cardpick_status = game._process_round_end_actions("efeeg")
        assert not cardpick_status

    def test_process_round_end_actions_slap_steal(self, monkeypatch):
        """
        Test _process_round_end_actions method of Game when card stack is stolen by a slap.
        """
        game = Game()
        n_players = 2
        # Patch the built-in 'input' function to provide unique keys for each player
        steal_slap_key = "d"
        user_inputs = iter([str(n_players), "a", "b", "c", steal_slap_key])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        game._setup_game()

        # Setup initial winner with no cards
        loser_idx = 0
        game._players[loser_idx].card_stack = CardDeck(nDecks=0)

        # Setup stealer to have no cards
        winner_idx = 1
        game._players[winner_idx].card_stack = CardDeck(nDecks=0)

        # Setup round stack that can be slapped
        game._round_stack.played_card_stack.add_card(Card("jack", "hearts"))
        game._round_stack.played_card_stack.add_card(Card("jack", "spades"))

        # Test processing player actions
        game._round_winner = loser_idx
        cardpick_status = game._process_round_end_actions(steal_slap_key)
        assert cardpick_status
        assert game._players[winner_idx].card_stack.nCards == 2
        assert game._players[loser_idx].card_stack.nCards == 0
