import copy
import concurrent.futures
import time
from board import Board
from config import BLACK, WHITE


def score_move(engine, board, move):
    """Heuristic used for move‑ordering."""
    clone = board.copy()
    clone.make_move(*move)
    r, c = move

    # Corners are king
    if move in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        return 10_000
    # Edges next
    if r in (0, 7) or c in (0, 7):
        return 3_000 + engine.static_eval(clone)
    # X‑squares are dangerous in Othello, discourage them a bit
    if (r, c) in [(1, 1), (1, 6), (6, 1), (6, 6)]:
        return -1_000
    return engine.static_eval(clone)


class Engine:
    """Othello engine with adjustable strength.

    strength = 1  → piece‑count only
    strength = 2  → corners / edges / mobility
    strength = 3  → + stability matrix
    strength = 4  → + TT move‑ordering hint
    """

    def __init__(self, color, strength: int = 4, time_limit: float = 0.5):
        self.color = color
        self.strength = max(1, min(strength, 4))
        self.time_limit = time_limit
        self.transposition: dict[str, dict] = {}
        self.node_counter: int = 0

    # ---------------------------------------------------------------------
    # Evaluation helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _dynamic_weights(board):
        total = sum(cell is not None for row in board.grid for cell in row)
        phase = total / 64  # 0→opening, 1→endgame
        return (
            int(10 * (1 - phase)) + 1,   # mobility
            int(100 * (1 - phase)) + 50, # corners
            int(20 * (1 - phase)) + 5,   # edges
            int(40 * phase) + 10         # stability
        )

    def static_eval(self, board):
        """Return a heuristic evaluation from the perspective of `self.color`."""
        if self.strength == 1:
            black, white = board.count_pieces()
            return (white - black) if self.color == WHITE else (black - white)

        mob_w, cor_w, edge_w, stab_w = self._dynamic_weights(board)

        # Corner / edge counts ------------------------------------------------
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        edges = [(0, c) for c in range(8)] + [(7, c) for c in range(8)] + \
                [(r, 0) for r in range(8)] + [(r, 7) for r in range(8)]
        my_corners = sum(board.grid[r][c] == self.color for r, c in corners)
        opp_corners = sum(board.grid[r][c] not in (None, self.color) for r, c in corners)
        my_edges = sum(board.grid[r][c] == self.color for r, c in edges)
        opp_edges = sum(board.grid[r][c] not in (None, self.color) for r, c in edges)

        # Mobility -----------------------------------------------------------
        current = board.current_player
        board.current_player = self.color
        my_moves = len(board.get_valid_moves())
        board.current_player = WHITE if self.color == BLACK else BLACK
        opp_moves = len(board.get_valid_moves())
        board.current_player = current

        # Piece differential -------------------------------------------------
        black, white = board.count_pieces()
        my_pieces = white if self.color == WHITE else black
        opp_pieces = black if self.color == WHITE else white

        # Stability (strength ≥3) -------------------------------------------
        stability_score = 0
        if self.strength >= 3:
            stab = [
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
                    val = stab[r][c]
                    if board.grid[r][c] == self.color:
                        stability_score += val
                    elif board.grid[r][c] not in (None, self.color):
                        stability_score -= val

        return (
            cor_w * (my_corners - opp_corners)
            + edge_w * (my_edges - opp_edges)
            + mob_w * (my_moves - opp_moves)
            + (my_pieces - opp_pieces)
            + (stab_w * stability_score if self.strength >= 3 else 0)
        )

    # ---------------------------------------------------------------------
    # Search
    # ---------------------------------------------------------------------
    def negamax(self, board, depth, alpha, beta, color):
        key = board.board_hash() + str(board.current_player)
        cache = self.transposition.get(key)
        if cache and cache['depth'] >= depth:
            return cache['score'], cache['move']

        moves = board.get_valid_moves()
        if depth == 0 or not moves:
            return color * self.static_eval(board), None

        # Move ordering ------------------------------------------------------
        if self.strength == 4:
            hint = cache['move'] if cache else None
            if hint in moves:
                moves.remove(hint)
                moves = [hint] + sorted(moves, key=lambda m: score_move(self, board, m), reverse=True)
            else:
                moves.sort(key=lambda m: score_move(self, board, m), reverse=True)
        else:
            moves.sort(key=lambda m: score_move(self, board, m), reverse=True)

        best_move = None
        max_score = -float('inf')
        for move in moves:
            self.node_counter += 1
            child = board.copy()
            child.make_move(*move)
            score, _ = self.negamax(child, depth - 1, -beta, -alpha, -color)
            score = -score
            if score > max_score:
                max_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        self.transposition[key] = {'score': max_score, 'move': best_move, 'depth': depth}
        return max_score, best_move

    # ---------------------------------------------------------------------
    # Root call with iterative deepening & threading
    # ---------------------------------------------------------------------
    def get_best_move(self, board):
        moves = board.get_valid_moves()
        if not moves:
            return None

        start = time.time()
        best_move = None
        depth = 1
        self.node_counter = 0

        while True:
            if time.time() - start > self.time_limit:
                break

            def eval_move(m):
                child = board.copy()
                child.make_move(*m)
                score, _ = self.negamax(child, depth - 1, -float('inf'), float('inf'), -1)
                return -score, m

            best_score = -float('inf')
            current_best = None

            with concurrent.futures.ThreadPoolExecutor() as ex:
                for score, m in ex.map(eval_move, moves):
                    if score > best_score:
                        best_score, current_best = score, m
                    if time.time() - start > self.time_limit:
                        break

            if time.time() - start <= self.time_limit:
                best_move = current_best
                depth += 1
            else:
                break
        return best_move
