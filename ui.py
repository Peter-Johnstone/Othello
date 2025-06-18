import pygame
import pygame.gfxdraw
from config import *

def draw_ui(win, gm):
    board = gm.board
    win.fill(GREEN)

    eval_score = gm.ai.static_eval(board)
    pct = max(min((eval_score + 1000) / 2000, 1), 0)
    pygame.draw.rect(win, DARK_GRAY, (10, 0, 20, HEIGHT))
    pygame.draw.rect(win, WHITE, (10, 0, 20, HEIGHT * pct))

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