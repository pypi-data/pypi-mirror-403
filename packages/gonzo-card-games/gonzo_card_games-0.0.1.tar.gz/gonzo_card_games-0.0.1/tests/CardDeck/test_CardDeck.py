import pytest

from gonzo_card_games.CardDeck import CardDeck, Card


class TestCardDeck:
    """
    Test functionality of the CardDeck class.
    """

    def test_cards_setter_invalid_type(self):
        """
        Test setting cards to an invalid type raises an error.
        """
        deck = CardDeck()
        with pytest.raises(TypeError):
            deck.cards = "not_a_list"

    def test_cards_setter_valid_cards(self):
        """
        Test setting cards to a list of cards works as expected.
        """
        deck = CardDeck(nDecks=0)
        cards = [Card(value="2", suit="hearts"), Card(value="3", suit="diamonds")]
        deck.cards = cards
        for i in range(len(cards)):
            assert deck.cards[i] is cards[i]

    def test_cards_getter_returns_copy(self):
        """
        Test that the cards getter returns a copy of the list of cards.
        """
        deck = CardDeck()
        cards_copy = deck.cards
        # modify the returned list
        cards_copy.append(Card(value="4", suit="clubs"))
        # check that original deck's cards list is unchanged
        assert deck.nCards != len(cards_copy)

    def test_unique_deck(self):
        """
        Test that a single deck contains 52 unique cards.
        """
        deck = CardDeck(nDecks=1)
        unique_cards = set((card.value, card.suit) for card in deck.cards)
        assert len(unique_cards) == deck.nCards == 52

    def test_deal_card_empty_deck(self):
        """
        Test dealing a card from an empty deck raises an error.
        """
        deck = CardDeck(nDecks=0)
        with pytest.raises(IndexError):
            deck.deal_card()

    def test_deal_card_from_bottom(self):
        """
        Test dealing a card from the bottom of the deck removes the expected card from the deck.
        """
        # setup deck and check which card is at the bottom
        deck = CardDeck()
        initial_nCards = deck.nCards
        expected_card = deck.cards[0]
        # deal card from bottom
        card = deck.deal_card(fromBottom=True)
        # check that card was removed from deck
        assert isinstance(card, Card)
        assert deck.nCards == initial_nCards - 1
        # check that card dealt is explicitly the one expected
        assert card is expected_card

    def test_deal_card_from_top(self):
        """
        Test dealing a card from the top of the deck removes the expected card from the deck.
        """
        # setup deck and check which card is at the top
        deck = CardDeck()
        initial_nCards = deck.nCards
        expected_card = deck.cards[-1]
        # deal card from top
        card = deck.deal_card(fromBottom=False)
        assert isinstance(card, Card)
        assert deck.nCards == initial_nCards - 1
        # check that card dealt is explicitly the one expected
        assert card is expected_card

    def test_see_card_invalid_index(self):
        """
        Test seeing a card with an invalid index raises an error.
        """
        deck = CardDeck()
        with pytest.raises(IndexError):
            deck.see_card(index=deck.nCards)

    def test_see_card_valid_index(self):
        """
        Test seeing a card with a valid index returns a copy of the expected card.
        """
        deck = CardDeck(nDecks=0)
        expected_card = Card(value="10", suit="spades")
        deck.add_card(expected_card)
        seen_card = deck.see_card(index=0)
        assert isinstance(seen_card, Card)
        # check that seen card is equal in value and suit to expected card
        assert seen_card == expected_card
        # check that seen card is a different instance than the one in the deck
        assert seen_card is not expected_card

    def test_add_card_invalid_type(self):
        """
        Test adding an invalid type as a card raises an error.
        """
        deck = CardDeck()
        with pytest.raises(TypeError):
            deck.add_card(card="not_a_card")

    def test_add_card_on_top(self):
        """
        Test adding a card on top of the deck.
        """
        # setup deck and add card
        deck = CardDeck()
        card = Card(value="5", suit="diamonds")
        initial_nCards = deck.nCards
        deck.add_card(card, onTop=True)
        assert deck.nCards == initial_nCards + 1
        # check that card on the top is explicitly the one added
        assert deck.cards[-1] is card

    def test_add_card_on_bottom(self):
        """
        Test adding a card on bottom of the deck.
        """
        # setup deck and add card
        deck = CardDeck()
        card = Card(value="king", suit="clubs")
        initial_nCards = deck.nCards
        deck.add_card(card, onTop=False)
        assert deck.nCards == initial_nCards + 1
        # check that card on the bottom is explicitly the one added
        assert deck.cards[0] is card

    def test_pull_card_invalid_index(self):
        """
        Test pulling a card with an invalid index raises an error.
        """
        deck = CardDeck()
        with pytest.raises(IndexError):
            deck.pull_card(index=deck.nCards)

    def test_pull_card_valid_index(self):
        """
        Test pulling a card with a valid index returns the expected card.
        """
        deck = CardDeck()
        initial_nCards = deck.nCards
        index = deck.nCards // 2
        expected_card = deck.cards[index]
        pulled_card = deck.pull_card(index=index)
        assert pulled_card is expected_card
        assert deck.nCards == initial_nCards - 1

    def test_insert_card_invalid_type(self):
        """
        Test inserting an invalid type as a card raises an error.
        """
        deck = CardDeck()
        with pytest.raises(TypeError):
            deck.insert_card(card="not_a_card", index=0)

    def test_insert_card_invalid_index(self):
        """
        Test inserting a card at an invalid index raises an error.
        """
        deck = CardDeck()
        card = Card(value="9", suit="diamonds")
        with pytest.raises(IndexError):
            deck.insert_card(card=card, index=-1)

    def test_insert_card_valid(self):
        """
        Test inserting a card at a valid index works as expected.
        """
        deck = CardDeck()
        card = Card(value="jack", suit="spades")
        index = deck.nCards // 2
        initial_nCards = deck.nCards
        deck.insert_card(card=card, index=index)
        assert deck.nCards == initial_nCards + 1
        assert deck.cards[index] is card

    def test_combine_decks_invalid_type(self):
        """
        Test combining an invalid type as a deck raises an error.
        """
        deck = CardDeck()
        with pytest.raises(TypeError):
            deck.combine_decks(other_deck="not_a_deck")

    def test_combine_decks_on_top(self):
        """
        Test combining two decks.
        """
        # setup decks and combine
        deck1 = CardDeck(nDecks=1)
        deck2 = CardDeck(nDecks=2)
        initial_nCards_deck1 = deck1.nCards
        deck1.combine_decks(other_deck=deck2, onTop=True)
        assert deck1.nCards == initial_nCards_deck1 + deck2.nCards
        # check that cards from deck2 are at the top of deck1
        for i in range(deck2.nCards):
            assert deck1.cards[initial_nCards_deck1 + i] is deck2.cards[i]

    def test_combine_decks_on_bottom(self):
        """
        Test combining two decks.
        """
        # setup decks and combine
        deck1 = CardDeck(nDecks=1)
        deck2 = CardDeck(nDecks=2)
        initial_nCards_deck1 = deck1.nCards
        deck1.combine_decks(other_deck=deck2, onTop=False)
        assert deck1.nCards == initial_nCards_deck1 + deck2.nCards
        # check that cards from deck2 are at the bottom of deck1
        for i in range(deck2.nCards):
            assert deck1.cards[i] is deck2.cards[i]

    def test_deal_deck(self):
        """
        Test dealing the deck into multiple piles gives even piles with unique instances of
        """
        # create deck of 3 unique instances of cards so that splitting into 2 piles leaves a card in the deck
        deck = CardDeck(nDecks=0)
        nPiles = 2
        card1 = Card(value="7", suit="hearts")
        card2 = Card(value="ace", suit="spades")
        card3 = Card(value="10", suit="clubs")
        deck.add_card(card1)
        deck.add_card(card2)
        deck.add_card(card3)
        nCards = deck.nCards
        # Split deck into piles and check that piles and deck all have correct number of cards
        piles = deck.deal_deck(nPiles=nPiles)
        assert len(piles) == nPiles
        assert piles[0].nCards == piles[1].nCards
        total_cards_in_piles = piles[0].nCards * nPiles
        assert total_cards_in_piles + deck.nCards == nCards
        # Check that all cards in piles and deck are unique instances
        card1 = piles[0].deal_card()
        card2 = piles[1].deal_card()
        card3 = deck.deal_card()
        assert card1 is not card2
        assert card1 is not card3
        assert card2 is not card3

    def test_str(self):
        """
        Test the __str__ method of the CardDeck class.
        """
        deck = CardDeck(nDecks=0)
        card1 = Card(value="5", suit="hearts")
        card2 = Card(value="7", suit="diamonds")
        deck.add_card(card1, onTop=True)
        deck.add_card(card2, onTop=True)
        str_repr = deck.__str__()
        assert (
            str_repr
            == f"CardDeck with {deck.nCards} cards: [{card1.__str__()}, {card2.__str__()}]"
        )

    def test_repr(self):
        """
        Test the __repr__ method of the CardDeck class.
        """
        deck = CardDeck(nDecks=1)
        repr_str = deck.__repr__()
        assert repr_str == f"CardDeck(nCards={deck.nCards})"
