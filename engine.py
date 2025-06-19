import copy
import concurrent.futures
import threading
import time
from board import Board
from config import BLACK, WHITE

def score_move(engine, board, move):
    """Heuristic used for move-ordering."""
    clone = board.copy()
    clone.make_move(*move)
    r, c = move

    if move in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        return 10_000
    if r in (0, 7) or c in (0, 7):
        return 3_000 + engine.static_eval(clone)
    if (r, c) in [(1, 1), (1, 6), (6, 1), (6, 6)]:
        return -1_000
    return engine.static_eval(clone)

class Engine:
    def __init__(self, color, strength: int = 4, time_limit: float = 0.5):
        self.color = color
        self.strength = max(1, min(strength, 4))
        self.time_limit = time_limit
        self.eval_bar_score = 0
        self.eval_thread = None
        self.eval_cancel = threading.Event()
        self.evaluating = False
        self.transposition: dict[str, dict] = {}
        self.node_counter: int = 0

    @staticmethod
    def _dynamic_weights(board):
        total = sum(cell is not None for row in board.grid for cell in row)
        phase = total / 64
        return (
            int(10 * (1 - phase)) + 1,
            int(100 * (1 - phase)) + 50,
            int(20 * (1 - phase)) + 5,
            int(40 * phase) + 10
        )


    def evaluate_position_async(self, board):
        active = threading.enumerate()
        print("Eval threads:", sum(t.name.startswith("Thread-") for t in active))
        if self.evaluating:  # ← still running → do nothing
            return

        # signal any previous run; DON'T clear self.evaluating here
        self.eval_cancel.set()

        # create a fresh cancel flag & mark ourselves running
        self.eval_cancel = threading.Event()
        self.evaluating = True

        def task():
            depth = 1
            cloned = board.copy()
            while not self.eval_cancel.is_set():
                score, _ = self.negamax(
                    cloned, depth,
                    -float('inf'), float('inf'), 1,
                    multithreaded=False,
                    stop_event=self.eval_cancel
                )
                if depth >= 5:
                    self.eval_bar_score = score
                depth += 1
                print(depth)
                time.sleep(0.05)
            self.evaluating = False  # ← mark finished

        self.eval_thread = threading.Thread(target=task, daemon=True)
        self.eval_thread.start()

    def stop_eval(self):
        """Request the background-eval thread to exit (non-blocking)."""
        self.eval_cancel.set()  # flag thread to stop
        # DON'T flip self.evaluating here—wait for thread to end

    def static_eval(self, board):
        if self.strength == 1:
            black, white = board.count_pieces()
            return (white - black) if self.color == WHITE else (black - white)

        mob_w, cor_w, edge_w, stab_w = self._dynamic_weights(board)

        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        edges = [(0, c) for c in range(8)] + [(7, c) for c in range(8)] + \
                [(r, 0) for r in range(8)] + [(r, 7) for r in range(8)]
        my_corners = sum(board.grid[r][c] == self.color for r, c in corners)
        opp_corners = sum(board.grid[r][c] not in (None, self.color) for r, c in corners)
        my_edges = sum(board.grid[r][c] == self.color for r, c in edges)
        opp_edges = sum(board.grid[r][c] not in (None, self.color) for r, c in edges)

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

    def negamax(self, board, depth, alpha, beta, color,
                multithreaded=True, stop_event: threading.Event | None = None):

        # ---------- EARLY CANCEL ----------
        if stop_event is not None and stop_event.is_set():
            return 0, None  # dummy score, caller will ignore
        # ----------------------------------

        key = board.board_hash() + str(board.current_player)
        cache = self.transposition.get(key)
        if cache and cache['depth'] >= depth:
            return cache['score'], cache['move']

        moves = board.get_valid_moves()
        if depth == 0 or not moves:
            return color * self.static_eval(board), None

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
            score, _ = self.negamax(child, depth - 1, -beta, -alpha, -color,
                                    multithreaded, stop_event)
            score = -score
            if score > max_score:
                max_score = score
                best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        self.transposition[key] = {'score': max_score, 'move': best_move, 'depth': depth}
        return max_score, best_move

    def get_best_move(self, board):
        """Return the best move found within self.time_limit.
        Guarantees at least a depth‑1 search so the engine never skips a turn.
        """
        moves = board.get_valid_moves()
        if not moves:
            return None

        # --- always do a depth‑1 scan first (no time limit) ---
        best_move = max(moves, key=lambda m: score_move(self, board, m))
        best_score = score_move(self, board, best_move)
        self.node_counter = 0  # reset for this call

        start = time.time()
        depth = 2  # we already did depth‑1 synchronously

        # iterative deepening within the allotted time
        while True:
            if time.time() - start >= self.time_limit:
                break

            def eval_move(m):
                child = board.copy()
                child.make_move(*m)
                score, _ = self.negamax(child, depth - 1, -float('inf'), float('inf'), -1, multithreaded=True)
                return -score, m

            best_depth_score = -float('inf')
            best_depth_move = None

            # multithread only if more than one move and time permits
            if len(moves) > 1 and self.time_limit - (time.time() - start) > 0.05:
                with concurrent.futures.ThreadPoolExecutor() as ex:
                    for score, m in ex.map(eval_move, moves):
                        if score > best_depth_score:
                            best_depth_score, best_depth_move = score, m
                        # time guard inside loop
                        if time.time() - start >= self.time_limit:
                            break
            else:  # single‑thread fall‑back
                for m in moves:
                    score, _ = self.negamax(board.copy(), depth - 1, -float('inf'), float('inf'), -1, multithreaded=False)
                    score = -score
                    if score > best_depth_score:
                        best_depth_score, best_depth_move = score, m
                    if time.time() - start >= self.time_limit:
                        break

            # if we completed the depth within time, adopt the new best
            if time.time() - start < self.time_limit and best_depth_move is not None:
                best_move, best_score = best_depth_move, best_depth_score
                depth += 1
            else:
                break

        return best_move
