import pygame
import pygame.gfxdraw
from config import *

def draw_ui(win, gm):
    board = gm.board
    win.fill(GREEN)

    # ─── evaluation bar (smooth) ──────────────────────────────────
    raw_pct = (gm.bar_ai.eval_bar_score + 1000) / 2000
    raw_pct = max(0.0, min(raw_pct, 1.0))

    # keep a float for sub-pixel smoothing
    if not hasattr(gm, "smooth_pct"):
        gm.smooth_pct = raw_pct
        gm.last_frame  = pygame.time.get_ticks()
    else:
        now   = pygame.time.get_ticks()
        dt    = (now - gm.last_frame) / 1000.0     # seconds
        gm.last_frame = now

        # time-based exponential smoothing:
        # half-life ≈ 0.25 s  → lambda = ln(2)/0.25
        halflife = 0.25
        lam      = 0.693 / halflife
        factor   = 1 - pow(2.71828, -lam * dt)

        gm.smooth_pct += (raw_pct - gm.smooth_pct) * factor

    # draw using the *float* height, rounded at the last moment
    bar_height = int(HEIGHT * gm.smooth_pct + 0.5)
    pygame.draw.rect(win, DARK_GRAY, (10, 0, 20, HEIGHT))
    pygame.draw.rect(win, WHITE,     (10, HEIGHT - bar_height, 20, bar_height))


    # kick off background evaluation if idle
    if not gm.bar_ai.evaluating:
        gm.bar_ai.evaluate_position_async(board)

    # ── board drawing …  (unchanged) ────────────────────────────────


    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * SQUARE_SIZE + 40, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            if gm.selected_move == (r, c):
                color = HINT_COLOR if gm.hint_active else SELECT_COLOR
                pygame.draw.rect(win, color, rect)
            else:
                pygame.draw.rect(win, GREEN, rect)
            pygame.draw.rect(win, LINE_COLOR, rect, 1)
            center = rect.center
            val = board.grid[r][c]
            if val == BLACK:
                pygame.gfxdraw.filled_circle(win, center[0], center[1], SQUARE_SIZE//2 - 6, BLACK)
                pygame.gfxdraw.aacircle(win, center[0], center[1], SQUARE_SIZE//2 - 6, BLACK)
            elif val == WHITE:
                pygame.gfxdraw.filled_circle(win, center[0], center[1], SQUARE_SIZE//2 - 6, WHITE)
                pygame.gfxdraw.aacircle(win, center[0], center[1], SQUARE_SIZE//2 - 6, WHITE)

    # Sidebar
    sidebar_x = BOARD_WIDTH + 40
    pygame.draw.rect(win, GRAY, (sidebar_x, 0, MENU_WIDTH, HEIGHT))
    label = FONT.render("Black's Turn" if board.current_player == BLACK else "White's Turn", True, BLACK)
    win.blit(label, (sidebar_x + 10, 20))

    black_count, white_count = board.count_pieces()
    score_label = BUTTON_FONT.render(f"Black: {black_count}  White: {white_count}", True, BLACK)
    win.blit(score_label, (sidebar_x + 10, 60))

    if gm.game_over:
        end_label = FONT.render(gm.winner, True, RED)
        win.blit(end_label, (sidebar_x + 10, 100))

    if gm.ai_thinking:
        thinking_label = BUTTON_FONT.render("AI Thinking...", True, BLUE)
        win.blit(thinking_label, (sidebar_x + 10, 300))

    # Buttons
    pygame.draw.rect(win, DARK_GRAY, gm.move_button_rect, border_radius=8)
    pygame.draw.rect(win, LINE_COLOR, gm.move_button_rect, 2, border_radius=8)
    win.blit(BUTTON_FONT.render("Perform Move", True, WHITE), (gm.move_button_rect.x + 15, gm.move_button_rect.y + 10))

    pygame.draw.rect(win, DARK_GRAY, gm.hint_button_rect, border_radius=8)
    pygame.draw.rect(win, LINE_COLOR, gm.hint_button_rect, 2, border_radius=8)
    win.blit(BUTTON_FONT.render("Hint", True, WHITE), (gm.hint_button_rect.x + 57, gm.hint_button_rect.y + 10))

    pygame.draw.rect(win, DARK_GRAY, gm.restart_button_rect, border_radius=8)
    pygame.draw.rect(win, LINE_COLOR, gm.restart_button_rect, 2, border_radius=8)
    win.blit(BUTTON_FONT.render("Restart", True, WHITE), (gm.restart_button_rect.x + 47, gm.restart_button_rect.y + 10))

    pygame.display.flip()
