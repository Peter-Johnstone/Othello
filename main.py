import pygame
import sys

from kiwisolver import strength

from config import *
from game_manager import GameManager
from ui import draw_ui
import time
from engine import Engine
from board import Board
from config import BLACK


def main():
    clock = pygame.time.Clock()
    gm = GameManager()
    running = True

    while running:
        if not gm.board.get_valid_moves():
            gm.board.current_player = WHITE if gm.board.current_player == BLACK else BLACK
            if gm.board.current_player == WHITE:
                gm.run_ai()
            if not gm.board.get_valid_moves():
                gm.game_over = True
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
                    hint_engine = Engine(gm.board.current_player, strength=4, time_limit=1.5)
                    hint = hint_engine.get_best_move(gm.board)

                    if hint:
                        gm.selected_move = hint
                        gm.hint_active = True
                        pygame.time.set_timer(pygame.USEREVENT, 1000)
                elif gm.restart_button_rect.collidepoint(x, y):
                    gm.restart()

    pygame.quit()
    sys.exit()





def test_engine_strength_comparison():
    board = Board()
    board.current_player = BLACK

    engine3 = Engine(BLACK, strength=3, time_limit=1.0)
    engine4 = Engine(BLACK, strength=4, time_limit=1.0)

    start3 = time.time()
    move3 = engine3.get_best_move(board)
    time3 = time.time() - start3
    nodes3 = engine3.node_counter

    start4 = time.time()
    move4 = engine4.get_best_move(board)
    time4 = time.time() - start4
    nodes4 = engine4.node_counter

    print("=== Engine Strength Comparison ===")
    print(f"Strength 3 → Move: {move3}, Time: {time3:.2f}s, Nodes: {nodes3}")
    print(f"Strength 4 → Move: {move4}, Time: {time4:.2f}s, Nodes: {nodes4}")
    print(f"Improvement: {nodes3 - nodes4} fewer nodes with strength 4" if nodes4 < nodes3 else f"Strength 4 searched more nodes.")


if __name__ == '__main__':
    main()
