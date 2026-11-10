"""Controller layer for MICO Tennis."""


class GameController:
    """Controller: routes user input to the model and game actions."""

    def __init__(self, game_context, model, view):
        self.game = game_context
        self.model = model
        self.view = view

    def handle_menu(self, events):
        self.game.handle_menu_events(events)

    def handle_game_input(self, events):
        """Process window, pause, restart, and serve input for one frame."""
        g = self.game
        pygame = g.pygame
        space_pressed = False
        for event in events:
            if event.type == pygame.QUIT:
                g.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    g.paused = not g.paused
                elif event.key == pygame.K_r and g.match_over:
                    self.model.restart_match()
                elif event.key == pygame.K_SPACE:
                    space_pressed = True
            elif (event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1 and g.paused):
                if g.pause_continue_rect.collidepoint(event.pos):
                    g.paused = False
                elif g.pause_quit_rect.collidepoint(event.pos):
                    g.paused = False
                    g.state = "menu"
                    g.menu_sel = 0
        return space_pressed

