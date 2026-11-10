"""View layer for MICO Tennis."""


class GameView:
    """View: renders menus, selection screens, and the paused game view."""

    def __init__(self, game_context, model):
        self.game = game_context
        self.model = model

    def render_menu_state(self):
        g = self.game
        if g.state in ("menu", "options"):
            g.draw_menu()
        elif g.state in ("select_player", "select_opp"):
            g.draw_select()
        elif g.state == "select_court":
            g.draw_court_select()
        elif g.state == "select_racket":
            g.draw_racket_select()

    def render_paused_game(self):
        g = self.game
        pygame = g.pygame
        g.draw_court()
        if g.serve_phase == "wait" and not g.match_over:
            g.draw_service_box(g.server, g.serve_deuce)
        if g.serve_mark and g.serve_mark[2] > 0:
            pygame.draw.ellipse(
                g.screen, g.LINE_WHITE,
                (int(g.serve_mark[0]) - 11, int(g.serve_mark[1]) - 5, 22, 10), 2,
            )
        g.draw_player(g.p2, 0.7)
        if g.ball_y < 300:
            g.draw_ball()
        g.draw_net()
        if g.ball_y >= 300:
            g.draw_ball()
        g.draw_player(g.p1, 1.1)
        g.draw_scoreboard()
        g.blit_center("PAUSED", g.big_font, g.WHITE, g.WIDTH // 2, 70)
        mouse_pos = pygame.mouse.get_pos()
        g.draw_button(g.pause_continue_rect, "CONTINUE",
                      g.pause_continue_rect.collidepoint(mouse_pos))
        g.draw_button(g.pause_quit_rect, "QUIT TO MENU",
                      g.pause_quit_rect.collidepoint(mouse_pos))
        g.blit_center("ESC = continue", g.tiny_font, g.GLOW_GREEN, g.WIDTH // 2, 325)
