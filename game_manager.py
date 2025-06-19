import copy
import threading
import pygame
from kiwisolver import strength

from board import Board
from engine import Engine
from config import WHITE, BLACK, WIDTH, MENU_WIDTH

class GameManager:
    def __init__(self):
        self.board = Board()
        self.ai = Engine(WHITE)
        self.bar_ai = Engine(WHITE)
        self.selected_move = None
        self.hint_active = False
        self.game_over = False
        self.ai_thinking = False
        self.winner = None
        self.history = []
        self.move_button_rect = pygame.Rect(WIDTH - MENU_WIDTH + 50, 100, 150, 40)
        self.hint_button_rect = pygame.Rect(WIDTH - MENU_WIDTH + 50, 147, 150, 40)
        self.restart_button_rect = pygame.Rect(WIDTH - MENU_WIDTH + 50, 194, 150, 40)
        self.ai_thread = None
        self.eval_thread = None
        self.eval_cancel = threading.Event()


    def start_ai(self):
        if self.board.current_player == WHITE and not self.ai_thinking:
            self.stop_eval_thread()  # Force stop eval before AI
            self.ai_thinking = True
            self.ai_thread = threading.Thread(target=self.run_ai)
            self.ai_thread.start()

    def stop_eval_thread(self):
        print("yo stopping")
        self.bar_ai.stop_eval()  # ❶ stop any old eval thread

    def start_eval_thread(self):
        print("yo stopping1")
        self.stop_eval_thread()  # safety: be sure the old one is gone
        self.bar_ai.evaluate_position_async(self.board)  # ❷ start fresh

    # ――― player (black) move ―――
    def play_move(self, row, col):
        if self.board.make_move(row, col):
            self.history.append(copy.deepcopy(self.board))
            self.selected_move = None
            self.start_eval_thread()  # ❸ restart bar-eval

            if not self.check_game_end():
                self.start_ai()
    def run_ai(self):
        move = self.ai.get_best_move(self.board)
        if move and self.board.current_player == WHITE:
            self.board.make_move(*move)
            self.history.append(copy.deepcopy(self.board))
        self.ai_thinking = False
        self.check_game_end()
        if not self.game_over:  # ❹ restart bar-eval
            print("nerd")
            self.start_eval_thread()

    def check_game_end(self):
        if not self.board.get_valid_moves():
            self.board.current_player = WHITE if self.board.current_player == BLACK else BLACK
            if not self.board.get_valid_moves():
                self.game_over = True
                b, w = self.board.count_pieces()
                if b > w:
                    self.winner = "Black Wins!"
                elif w > b:
                    self.winner = "White Wins!"
                else:
                    self.winner = "Draw"
                return True
        return False

    def restart(self):
        self.stop_eval_thread()
        self.__init__()
