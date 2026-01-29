from gonzo_card_games.Templates import CardGameTemplate


class TestCardGameTemplate:
    """
    Provide test coverage for CardGameTemplate class
    """

    def test_provide_coverage(self):
        """
        Provide test coverage for template class
        """
        template = CardGameTemplate()
        template.print_rules()
        template.print_controls()
        template.play_game()
