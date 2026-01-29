from gonzo_card_games import RatScrew


class DockerCardGamesRunner:
    """
    Class to ochestrate playing suite of card games in Docker container
    """

    def __init__(self) -> None:
        """
        Initialize instance of DockerCardGamesRunner
        """
        self._game_options = [RatScrew.Game]
        self._reset_game_selection()

    def run_card_games(self) -> None:
        while True:
            # Get game to play
            self._run_game_selection()
            if self._game_runner is None:
                print("Hope you enjoyed playing card games!")
                return
            # Run game actions
            while self._game_runner:
                self._run_game_action()

    def _reset_game_selection(self) -> None:
        """Reset game selection state"""
        self._game_runner = None

    def _run_game_selection(self) -> None:
        """
        Get user input for what game to play and update game selection state
        """
        print("Select game that you'd like to play")
        game_options = dict()
        for idx, game_class in enumerate(self._game_options):
            game = game_class()
            print(f"{idx+1}) {game._game_title}")
            game_options[str(idx + 1)] = self._set_game_selection
        print(f"{len(self._game_options)+1}) Quit")
        game_options[str(len(self._game_options) + 1)] = lambda x: None
        valid_selection = False
        while not valid_selection:
            selection = input(">").strip()
            game_selection = game_options.get(selection, None)
            if game_selection is not None:
                valid_selection = True
        game_selection(int(selection) - 1)

    def _set_game_selection(self, game_selection_idx: int) -> None:
        """
        Update game selection state

        game_selection_idx, int
            Index of game that selection state should be set to
        """
        if game_selection_idx >= len(self._game_options) or game_selection_idx < 0:
            self._reset_game_selection()
            return
        self._game_runner = self._game_options[game_selection_idx]()

    def _run_game_action(self) -> None:
        """
        Get user input for what game action should be done and run action
        """
        if self._game_runner is None:
            raise AttributeError(
                "Game must be selected before user actions can be requested"
            )
        action_options = {
            "1": self._game_runner.play_game,
            "2": self._game_runner.print_rules,
            "3": self._game_runner.print_controls,
            "4": self._reset_game_selection,
        }
        print(f"Select action for {self._game_runner._game_title}")
        print("1) Play game")
        print("2) See game rules")
        print("3) See game controls")
        print("4) Quit and select different game")
        valid_selection = False
        while not valid_selection:
            selection = input(">").strip()
            game_action = action_options.get(selection, None)
            if game_action is not None:
                valid_selection = True
        game_action()


if __name__ == "__main__":
    DockerCardGamesRunner().run_card_games()  # pragma: no cover
