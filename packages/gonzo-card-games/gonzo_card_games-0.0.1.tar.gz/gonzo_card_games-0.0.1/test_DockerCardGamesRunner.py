import pytest
from DockerCardGamesRunner import DockerCardGamesRunner


class TestDockerCardGamesRunner:
    """
    Test functionality of DockerCardGamesRunner class
    """

    def test_reset_game_selection(self):
        """
        Test _reset_game_selection method of DockerCardGamesRunner.
        """

        runner = DockerCardGamesRunner()
        runner._game_runner = "dummy"

        runner._reset_game_selection()
        assert runner._game_runner is None

    def test_run_game_selection(self, monkeypatch):
        """
        Test _run_game_selection method of DockerCardGamesRunner
        """
        runner = DockerCardGamesRunner()

        # override built-in input function to return test input
        user_inputs = iter(["-1", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        runner._run_game_selection()
        assert isinstance(runner._game_runner, runner._game_options[0])

    def test_set_game_selection_invalid(self):
        """
        Test _set_game_selection method of DockerCardGamesRunner when invalid game index is inputted
        """
        runner = DockerCardGamesRunner()

        # game index is too small
        runner._set_game_selection(-1)
        assert runner._game_runner is None
        # game index is greater than last game option
        runner._set_game_selection(len(runner._game_options))
        assert runner._game_runner is None

    def test_set_game_selection_valid(self):
        """
        Test _set_game_selection method of DockerCardGamesRunner when valid game index is inputted
        """
        runner = DockerCardGamesRunner()

        # game index is too small
        runner._set_game_selection(0)
        assert isinstance(runner._game_runner, runner._game_options[0])

    def test_run_game_action_no_game_select(self):
        """
        Test _run_game_action method of DockerCardGamesRunner when no game has been selected yet
        """
        runner = DockerCardGamesRunner()
        with pytest.raises(AttributeError):
            runner._run_game_action()

    def test_run_game_action_game_selected(self, monkeypatch):
        """
        Test _run_game_action method of DockerCardGamesRunner when game has been selected
        """
        runner = DockerCardGamesRunner()
        # Select game
        runner._game_runner = runner._game_options[0]()
        # override built-in input function to return test input
        user_inputs = iter(["-1", "4"])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))
        # Run method and ensure that quit action is successful (i.e., this test does not get stuck in infinite loop)
        runner._run_game_action()

    def test_run_card_game(self, monkeypatch):
        """
        Provide test coverage of run_card_game method of DockerCardGamesRunner
        """
        runner = DockerCardGamesRunner()

        # override built-in input function to return test input
        user_inputs = iter(["1", "4", str(len(runner._game_options) + 1)])
        monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

        runner.run_card_games()
