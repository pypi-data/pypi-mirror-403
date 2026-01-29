import pytest
from gonzo_card_games.CardDeck import CardDeck, Card
from gonzo_card_games.RatScrew import RoundCardStack


class TestRoundCardStack:
    """
    Test functionality of RoundCardStack class.
    """

    def test_reset(self):
        """
        Test reset method.
        """
        stack = RoundCardStack()
        # Update private attributes to all be None
        stack._played_card_stack = None
        stack._penalty_card_stack = None
        stack._need_face_card = None
        stack._face_card_countdown = None

        # Reset stack and verify all attributes are the expected default
        stack.reset()
        assert isinstance(stack._played_card_stack, CardDeck)
        assert stack._played_card_stack.nCards == 0
        assert isinstance(stack._penalty_card_stack, CardDeck)
        assert stack._penalty_card_stack.nCards == 0
        stack._need_face_card is False
        assert stack._face_card_countdown == 0

    def test_need_face_card(self):
        """
        Test need_face_card attribute property and setter
        """
        stack = RoundCardStack()
        random_val = 5
        stack._need_face_card = random_val
        assert stack.need_face_card == random_val
        with pytest.raises(AttributeError):
            stack.need_face_card = random_val

    def test_played_card_stack(self):
        """
        Test played_card_stack attribute property and setter
        """
        stack = RoundCardStack()
        random_val = 5
        stack._played_card_stack = random_val
        assert stack.played_card_stack == random_val
        with pytest.raises(AttributeError):
            stack.played_card_stack = random_val

    def test_penalty_card_stack(self):
        """
        Test penalty_card_stack attribute property and setter
        """
        stack = RoundCardStack()
        random_val = 5
        stack._penalty_card_stack = random_val
        assert stack.penalty_card_stack == random_val
        with pytest.raises(AttributeError):
            stack.penalty_card_stack = random_val

    def test_process_face_card_valid(self):
        """
        Test process_face_card method when valid face card is inputted
        """
        for card_val, attempts in [("jack", 1), ("queen", 2), ("king", 3), ("ace", 4)]:
            stack = RoundCardStack()
            stack._process_face_card(Card(value=card_val, suit="spades"))
            assert stack.need_face_card is True
            assert stack._face_card_countdown == attempts

    def test_process_face_card_invalid(self):
        """
        Test process_face_card method when non face card is inputted
        """
        with pytest.raises(ValueError):
            stack = RoundCardStack()
            stack._process_face_card(Card("2", "hearts"))

    def test_add_played_card_not_card(self):
        """
        Test add_played_card method when non-card instance is "played".
        """
        stack = RoundCardStack()
        not_a_card = True
        with pytest.raises(TypeError):
            stack.add_played_card(not_a_card)

    def test_add_played_card_face_card(self):
        """
        Test add_played_card method when a face card is played.
        """
        stack = RoundCardStack()
        face_card = Card("jack", "hearts")
        stack.add_played_card(face_card)
        assert stack.need_face_card is True
        assert stack._face_card_countdown == 1  # Jack allows 1 chance
        assert stack.played_card_stack.nCards == 1
        assert stack.penalty_card_stack.nCards == 0

    def test_add_played_card_non_face_card(self):
        """
        Test add_played_card method when a non-face card is played.
        """
        countdown_default = 0
        stack = RoundCardStack()
        assert stack._face_card_countdown == countdown_default
        non_face_card = Card("7", "clubs")
        stack.add_played_card(non_face_card)
        assert stack.need_face_card is False
        assert stack._face_card_countdown == countdown_default - 1
        assert stack.played_card_stack.nCards == 1
        assert stack.penalty_card_stack.nCards == 0

    def test_add_penalty_card_not_card(self):
        """
        Test add_penalty_card method when non-card instance is added.
        """
        stack = RoundCardStack()
        not_a_card = True
        with pytest.raises(TypeError):
            stack.add_penalty_card(not_a_card)

    def test_add_penalty_card(self):
        """
        Test add_penalty_card method.
        """
        stack = RoundCardStack()
        penalty_card = Card("king", "spades")
        stack.add_penalty_card(penalty_card)
        assert stack.penalty_card_stack.nCards == 1
        assert stack.played_card_stack.nCards == 0
        # check that face card countdown and need_face_card remain unchanged
        assert stack.need_face_card is False
        assert stack._face_card_countdown == 0

    def test_has_stack_been_won(self):
        """
        Test has_stack_been_won method.
        """
        stack = RoundCardStack()
        # Initially, stack should not be won
        assert stack.has_stack_been_won() is False

        # Simulate playing a face card and countdown reaching zero
        face_card = Card("queen", "diamonds")
        stack.add_played_card(face_card)
        stack._face_card_countdown = 0  # Manually set countdown to 0
        assert stack.has_stack_been_won() is True

        # Reset and test when countdown is still positive
        stack = RoundCardStack()
        stack.add_played_card(face_card)
        assert stack.has_stack_been_won() is False

    def test_is_valid_slap_double(self):
        """
        Test is_valid_slap method for valid double.
        """
        stack = RoundCardStack()
        # Initially, slap should be invalid
        assert stack.is_valid_slap() is False

        double_val = "5"
        # Add two cards that are not the same to make slap invalid
        stack.add_played_card(Card("3", "clubs"))
        stack.add_played_card(Card(double_val, "diamonds"))
        assert stack.is_valid_slap() is False
        # Add card with the same value as the last card to make a double
        stack.add_played_card(Card(double_val, "hearts"))
        assert stack.is_valid_slap() is True

    def test_is_valid_slap_sandwich(self):
        """
        Test is_valid_slap method for valid sandwich.
        """
        stack = RoundCardStack()
        # Initially, slap should be invalid
        assert stack.is_valid_slap() is False

        sandwich_val = "9"
        # Add three cards that don't make a sandwich
        stack.add_played_card(Card("7", "clubs"))
        stack.add_played_card(Card(sandwich_val, "hearts"))
        stack.add_played_card(Card("2", "diamonds"))
        assert stack.is_valid_slap() is False

        # Add card with the same value as the second card to make a sandwich
        stack.add_played_card(Card(sandwich_val, "spades"))
        assert stack.is_valid_slap() is True
