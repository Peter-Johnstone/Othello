import pygame
import sys

from kiwisolver import strength

from config import *
from game_manager import GameManager
from ui import draw_ui
from engine import Engine


def main():
    clock = pygame.time.Clock()
    gm = GameManager()
    running = True

    while running:
        draw_ui(WIN, gm)
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                gm.selected_move = None
                gm.hint_active = False
                pygame.time.set_timer(pygame.USEREVENT, 0)
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if x < BOARD_WIDTH + 40:
                    row, col = y // SQUARE_SIZE, (x - 40) // SQUARE_SIZE
                    if 0 <= row < 8 and 0 <= col < 8:
                        gm.selected_move = (row, col)
                        gm.hint_active = False
                elif gm.move_button_rect.collidepoint(x, y):
                    if gm.selected_move:
                        gm.play_move(*gm.selected_move)
                elif gm.hint_button_rect.collidepoint(x, y):
                    hint_engine = Engine(gm.board.current_player, strength=3)
                    hint = hint_engine.get_best_move(gm.board)
                    if hint:
                        gm.selected_move = hint
                        gm.hint_active = True
                        pygame.time.set_timer(pygame.USEREVENT, 1000)
                elif gm.restart_button_rect.collidepoint(x, y):
                    gm.restart()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
