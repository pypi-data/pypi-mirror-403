import pytest

from gonzo_card_games.CardDeck import Card


class TestCard:
    """
    Test functionality of the Card class.
    """

    def test_card_creation(self):
        """
        Test creating a valid card.
        """
        card = Card(value="2", suit="spades")
        assert card.value == "2"
        assert card.suit == "spades"

    def test_card_creation_not_case_sensitive(self):
        """
        Test creating a card with mixed case value and suit.
        """
        card = Card(value="qUeEn", suit="hEarts")
        assert card.value == "queen"
        assert card.suit == "hearts"

    def test_invalid_value(self):
        """
        Test that creating a card with an invalid value raises a ValueError.
        """
        with pytest.raises(ValueError):
            Card("11", "clubs")

    def test_invalid_suit(self):
        """
        Test that creating a card with an invalid suit raises a ValueError.
        """
        with pytest.raises(ValueError):
            Card("8", "stars")

    def test_same_suit(self):
        """
        Test that comparison between suits of cards works as expected.
        """
        card1 = Card(value="10", suit="diamonds")
        card2 = Card(value="3", suit="diamonds")
        card3 = Card(value="10", suit="hearts")
        # check that suits matching returns True
        assert card1.sameSuit(card2)
        # check that suits not matching returns False, regardless of value
        assert not card1.sameSuit(card3)

    def test_same_value(self):
        """
        Test that comparison between values of cards works as expected.
        """
        card1 = Card(value="jack", suit="clubs")
        card2 = Card(value="jack", suit="spades")
        card3 = Card(value="7", suit="clubs")
        # check that values matching returns True
        assert card1.sameValue(card2)
        # check that values not matching returns False, regardless of suit
        assert not card1.sameValue(card3)

    def test_is_face_card(self):
        """
        Test that isFaceCard method works as expected.
        """
        face_card = Card(value="king", suit="hearts")
        non_face_card = Card(value="9", suit="clubs")
        assert face_card.isFaceCard() is True
        assert non_face_card.isFaceCard() is False

    def test_card_equality_invalid_cards(self):
        """
        Test equality comparison between a card and a different type returns False.
        """
        card = Card(value="3", suit="diamonds")
        assert not card == "not_a_card"

    def test_card_equality_valid_cards(self):
        """
        Test equality comparison between two valid cards.
        """
        card1 = Card(value="2", suit="spades")
        card2 = Card(value="2", suit="spades")
        card3 = Card(value="king", suit="clubs")
        assert card1 == card2
        assert card1 != card3

    def test_str(self):
        """
        Test the string representation of a card.
        """
        card = Card(value="ace", suit="diamonds")
        assert card.__str__() == "Ace of Diamonds"

    def test_repr(self):
        """
        Test the repr representation of a card.
        """
        card = Card(value="ace", suit="diamonds")
        assert card.__repr__() == "Card(value='ace', suit='diamonds')"
