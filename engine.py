import copy
import concurrent.futures
import time
from board import Board
from config import ROWS, COLS, BLACK, WHITE, DEPTH
from functools import lru_cache

class Engine:
    def __init__(self, color, strength=3):
        self.color = color
        self.transposition = {}

        self.strength = strength
        # 1(Basic): Just piece count.
        # 2(Medium): Corners, edges, and mobility.
        # 3(Strong): Adds stability matrix and dynamic weights.

    def dynamic_weights(self, board):
        total_pieces = sum(row.count(BLACK) + row.count(WHITE) for row in board.grid)
        phase = total_pieces / 64
        mobility_weight = int(10 * (1 - phase)) + 1
        corner_weight = int(100 * (1 - phase)) + 50
        edge_weight = int(20 * (1 - phase)) + 5
        stability_weight = int(40 * phase) + 10
        return mobility_weight, corner_weight, edge_weight, stability_weight

    def static_eval(self, board):
        if self.strength == 1:
            black, white = board.count_pieces()
            return (white - black) if self.color == WHITE else (black - white)

        mobility_weight, corner_weight, edge_weight, stability_weight = self.dynamic_weights(board)

        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        edges = [(0, c) for c in range(8)] + [(7, c) for c in range(8)] + [(r, 0) for r in range(8)] + [(r, 7) for r in range(8)]
        my_corners = sum(1 for r, c in corners if board.grid[r][c] == self.color)
        opp_corners = sum(1 for r, c in corners if board.grid[r][c] not in (self.color, None))
        my_edges = sum(1 for r, c in edges if board.grid[r][c] == self.color)
        opp_edges = sum(1 for r, c in edges if board.grid[r][c] not in (self.color, None))

        current = board.current_player
        board.current_player = self.color
        my_moves = len(board.get_valid_moves())
        board.current_player = WHITE if self.color == BLACK else BLACK
        opp_moves = len(board.get_valid_moves())
        board.current_player = current

        black, white = board.count_pieces()
        my_pieces = white if self.color == WHITE else black
        opp_pieces = black if self.color == WHITE else white

        stability_score = 0
        if self.strength >= 3:
            stability_matrix = [
                [4, -3, 2, 2, 2, 2, -3, 4],
                [-3, -4, -1, -1, -1, -1, -4, -3],
                [2, -1, 1, 0, 0, 1, -1, 2],
                [2, -1, 0, 1, 1, 0, -1, 2],
                [2, -1, 0, 1, 1, 0, -1, 2],
                [2, -1, 1, 0, 0, 1, -1, 2],
                [-3, -4, -1, -1, -1, -1, -4, -3],
                [4, -3, 2, 2, 2, 2, -3, 4],
            ]
            for r in range(8):
                for c in range(8):
                    if board.grid[r][c] == self.color:
                        stability_score += stability_matrix[r][c]
                    elif board.grid[r][c] not in (None, self.color):
                        stability_score -= stability_matrix[r][c]

        return (
            corner_weight * (my_corners - opp_corners) +
            edge_weight * (my_edges - opp_edges) +
            mobility_weight * (my_moves - opp_moves) +
            (my_pieces - opp_pieces) +
            (stability_weight * stability_score if self.strength >= 3 else 0)
        )

    def negamax(self, board, depth, alpha, beta, color):
        key = board.board_hash() + str(board.current_player)
        if key in self.transposition and self.transposition[key]['depth'] >= depth:
            return self.transposition[key]['score'], self.transposition[key]['move']

        valid_moves = board.get_valid_moves()
        if depth == 0 or not valid_moves:
            return color * self.static_eval(board), None

        valid_moves.sort(key=lambda m: score_move(self, board, m), reverse=True)

        max_score = -float('inf')
        best_move = None
        for move in valid_moves:
            clone = board.copy()
            clone.make_move(*move)
            score, _ = self.negamax(clone, depth - 1, -beta, -alpha, -color)
            score = -score
            if score > max_score:
                max_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        self.transposition[key] = {'score': max_score, 'move': best_move, 'depth': depth}
        return max_score, best_move

    def get_best_move(self, board, time_limit=1.5):
        valid_moves = board.get_valid_moves()
        if not valid_moves:
            return None

        start_time = time.time()
        best_move = None
        max_depth = 1

        while True:
            if time.time() - start_time > time_limit:
                break

            current_best = None
            max_score = -float('inf')
            alpha, beta = -float('inf'), float('inf')
            for move in sorted(valid_moves, key=lambda m: score_move(self, board, m), reverse=True):
                clone = board.copy()
                clone.make_move(*move)
                score, _ = self.negamax(clone, max_depth - 1, -beta, -alpha, -1)
                score = -score
                if score > max_score:
                    max_score = score
                    current_best = move
                alpha = max(alpha, score)
                if time.time() - start_time > time_limit:
                    break

            if time.time() - start_time <= time_limit:
                best_move = current_best
                max_depth += 1
            else:
                break

        return best_move

def score_move(engine, board, move):
    clone = board.copy()
    clone.make_move(*move)
    r, c = move

    # Prioritize strong positions
    if move in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        return 10000
    elif r in (0, 7) or c in (0, 7):
        return 3000 + engine.static_eval(clone)
    elif (r in (1, 6) and c in (1, 6)):
        return -1000  # avoid dangerous x-squares
    return engine.static_eval(clone)
