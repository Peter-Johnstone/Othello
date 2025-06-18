import pygame

# Constants
MENU_WIDTH = 180
BOARD_WIDTH = 640
WIDTH, HEIGHT = BOARD_WIDTH + MENU_WIDTH, 640
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS
DEPTH = 5

# Colors
GREEN = (0, 150, 0)
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
GRAY = (230, 230, 230)
DARK_GRAY = (60, 60, 60)
LIGHT_BLACK = (80, 80, 80)
LIGHT_WHITE = (220, 220, 220)
LINE_COLOR = (10, 10, 10)
HINT_COLOR = (209, 255, 189)
SELECT_COLOR = (255, 215, 0)
BLUE = (50, 150, 255)
RED = (255, 50, 50)

# Initialize Pygame
pygame.init()
WIN = pygame.display.set_mode((WIDTH + 40, HEIGHT))
pygame.display.set_caption("Othello Enhanced")
FONT = pygame.font.SysFont("arial", 24, bold=True)
BUTTON_FONT = pygame.font.SysFont("arial", 18, bold=True)
