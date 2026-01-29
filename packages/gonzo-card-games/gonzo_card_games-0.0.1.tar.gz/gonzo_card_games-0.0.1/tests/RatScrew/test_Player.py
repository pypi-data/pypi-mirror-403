import pytest

from gonzo_card_games.CardDeck import Card, CardDeck
from gonzo_card_games.RatScrew import RoundCardStack, Player


class MockPlayer(Player):
    """Mock class of Player that can directly set play and slap keys"""

    def __init__(self, play_key="a", slap_key="b"):
        self._play_key = play_key
        self._slap_key = slap_key
        self.card_stack = CardDeck(nDecks=0)


class TestPlayer:
    """
    Test functionality of Player class.
    """

    def test_is_valid_action_key_with_no_constraints(self):
        """
        Test is_valid_action_key static method of Player when constraints are not applied for which keys are invalid.
        """
        # Test with no constraints on which keys are invalid
        assert Player._is_valid_action_key("a") is True
        assert Player._is_valid_action_key("ab") is False

    def test_is_valid_action_key_with_constraints(self):
        """
        Test is_valid_action_key static method of Player when constraints are applied for which keys are invalid.
        """

        # Test with constraints on which keys are invalid
        invalid_keys = {"x", "y", "z"}
        assert Player._is_valid_action_key("x", invalid_keys) is False
        assert Player._is_valid_action_key("a", invalid_keys) is True
        assert Player._is_valid_action_key("yz", invalid_keys) is False
        assert Player._is_valid_action_key("bc", invalid_keys) is False

    def test_init(self, monkeypatch, invalid_action_keys=None):
        """
        Test initialization of Player.
        """

        # sequence of user inputs for play and slap keys, invalid input followed by valid input
        play_key = "a"
        slap_key = "b"
        user_inputs = ["foo", play_key, "bar", slap_key]
        inputs = iter(user_inputs)

        # Patch the built-in 'input' function to use the iterator
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        player = Player(invalid_action_keys)
        assert player.play_key == play_key
        assert player.slap_key == slap_key
        assert player.card_stack.nCards == 0

    def test_init_with_existing_invalid_keys(self, monkeypatch):
        """
        Add test coverage for initialization of Player with existing invalid action keys.
        """
        # pre-existing invalid keys that will be checked against during initialization
        existing_invalid_keys = {"x", "y", "z"}
        # rerun the init test with these existing invalid keys
        self.test_init(monkeypatch, existing_invalid_keys)

    def test_play_key(self):
        """
        Test play_key attribute property and setter
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        random_val = "a"
        player._play_key = random_val
        assert player.play_key == random_val
        with pytest.raises(AttributeError):
            player.play_key = random_val

    def test_slap_key(self):
        """
        Test slap_key attribute property and setter
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        random_val = "a"
        player._slap_key = random_val
        assert player.slap_key == random_val
        with pytest.raises(AttributeError):
            player.slap_key = random_val

    def test_card_stack(self):
        """
        Test card_stack attribute property and setter
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        random_deck = CardDeck()
        not_a_deck = True
        player.card_stack = random_deck
        assert player.card_stack is random_deck
        with pytest.raises(TypeError):
            player.card_stack = not_a_deck

    def test_play_card_no_cards(self):
        """
        Test playing a card when player has no cards.
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        with pytest.raises(IndexError):
            player.play_card()

    def test_play_card_valid(self):
        """
        Test playing a card when player has no cards.
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        expected_card = Card("5", "hearts")
        player.card_stack.add_card(expected_card)
        assert player.play_card() == expected_card

    def test_take_round_stack_invalid(self):
        """
        Test take_round_stack method when invalid stack is inputted
        """
        # Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        not_a_card_stack = True
        with pytest.raises(TypeError):
            player.take_round_stack(not_a_card_stack)

    def test_take_round_stack_valid(self):
        """
        Test take_round_stack method when valid stack is inputted
        """
        # Generate cards to add to player stack and round stack
        played_card = Card("2", "spades")
        penalty_card = Card("8", "hearts")
        last_card = Card("ace", "diamonds")

        # Add cards to player stack and round staack
        ## Use mock class since play and slap keys set don't matter
        player = MockPlayer()
        player.card_stack.add_card(last_card)
        round_stack = RoundCardStack()
        round_stack.add_played_card(played_card)
        round_stack.add_penalty_card(penalty_card)

        # Give player stack and verify order of cards is correct
        player.take_round_stack(round_stack)
        assert player.card_stack.nCards == 3
        assert player.card_stack.see_card(0) == played_card
        assert player.card_stack.see_card(1) == penalty_card
        assert player.card_stack.see_card(2) == last_card
        assert round_stack.played_card_stack.nCards == 0
        assert round_stack.penalty_card_stack.nCards == 0
