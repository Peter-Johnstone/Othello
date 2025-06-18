import copy
import hashlib
from config import ROWS, COLS, BLACK, WHITE

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.grid[3][3] = WHITE
        self.grid[4][4] = WHITE
        self.grid[3][4] = BLACK
        self.grid[4][3] = BLACK
        self.current_player = BLACK
        self.selected = None

    def board_hash(self):
        flat = ''.join(['.' if cell is None else ('B' if cell == BLACK else 'W') for row in self.grid for cell in row])
        return hashlib.sha256(flat.encode()).hexdigest()

    def copy(self):
        return copy.deepcopy(self)

    def count_pieces(self):
        black = sum(row.count(BLACK) for row in self.grid)
        white = sum(row.count(WHITE) for row in self.grid)
        return black, white

    def inside_board(self, r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def valid_move(self, row, col):
        if self.grid[row][col] is not None:
            return False
        opponent = WHITE if self.current_player == BLACK else BLACK
        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found = False
            while self.inside_board(r,c) and self.grid[r][c] == opponent:
                r += dr
                c += dc
                found = True
            if found and self.inside_board(r,c) and self.grid[r][c] == self.current_player:
                return True
        return False

    def get_valid_moves(self):
        return [(r,c) for r in range(ROWS) for c in range(COLS) if self.valid_move(r,c)]

    def make_move(self, row, col):
        if not self.valid_move(row, col):
            return False
        self.grid[row][col] = self.current_player
        opponent = WHITE if self.current_player == BLACK else BLACK
        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            to_flip = []
            while self.inside_board(r,c) and self.grid[r][c] == opponent:
                to_flip.append((r,c))
                r += dr
                c += dc
            if self.inside_board(r,c) and self.grid[r][c] == self.current_player:
                for fr, fc in to_flip:
                    self.grid[fr][fc] = self.current_player
        self.current_player = opponent
        return True
