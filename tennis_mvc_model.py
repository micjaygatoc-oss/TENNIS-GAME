"""Model layer for MICO Tennis."""


class GameModel:
    """Model: exposes match and menu state from the game context."""

    def __init__(self, game_context):
        self.game = game_context

    @property
    def screen_state(self):
        return self.game.state

    @property
    def is_running(self):
        return self.game.running

    @property
    def is_paused(self):
        return self.game.paused

    @property
    def is_match_over(self):
        return self.game.match_over

    def restart_match(self):
        self.game.reset_match()
