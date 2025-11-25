import pygame
import sys
import random

# To run: pip install pygame
# python3 connect_four.py

"""
        Simple computer AI with a three-tier strategy:

        1. WIN: First, the AI checks if it can win in the next move by trying each column
           and simulating placing its piece there. If any move results in 4-in-a-row,
           it immediately takes that winning move.

        2. BLOCK: If no winning move exists, the AI checks if the human player can win
           in their next move. It simulates placing the human's piece in each column
           and if any would result in a human win, it blocks that move.

        3. RANDOM: If neither winning nor blocking is possible, the AI makes a random
           move from all available valid columns.

        This creates a basic but effective AI that prevents obvious losses while
        capitalizing on immediate wins. The AI doesn't look ahead more than one move,
        making it beatable by more strategic human players.

        Based on the Connect Four game I created, here are the algorithms and AI structures being used:
        
1. Rule-Based AI (Expert System)
The computer AI uses a rule-based approach with a priority hierarchy:
Rule 1: If winning move exists → take it
Rule 2: If blocking move needed → take it
Rule 3: Otherwise → make random valid move
This is a simple expert system that follows predefined logical rules rather than learning.

2. Game Tree Search (Limited Depth)
The AI performs a 1-ply lookahead (one move ahead):
It simulates each possible move by creating temporary board states
Evaluates each simulated position for win/loss conditions
This is essentially a minimax algorithm with depth=1

3. Brute Force Search
For each move decision, the AI:
Iterates through all 7 possible columns
For each column, simulates the move
Checks all winning patterns (horizontal, vertical, diagonal)
This is a brute force approach that exhaustively checks all possibilities

4. State Space Search
The AI searches through the game state space:
Current board state → possible next states → evaluation
Uses forward simulation to predict outcomes
Implements immediate reward evaluation (win/lose/draw)

5. Pattern Recognition
The win detection uses pattern matching:
Searches for 4-in-a-row patterns in all directions
Uses template matching for win conditions
Implements sliding window approach to check sequences
 
This is a deterministic, rule-based AI that's essentially a sophisticated "if-then" system with basic game tree search. It's effective for Connect Four's simple rule set but would struggle with more complex games that require deeper strategic thinking.
"""

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600
BOARD_WIDTH = 7
BOARD_HEIGHT = 6
CELL_SIZE = 80
CELL_MARGIN = 5
BOARD_X_OFFSET = 50
BOARD_Y_OFFSET = 50

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)


class ConnectFour:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Connect Four")
        self.clock = pygame.time.Clock()

        # Game state
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_player = 1  # 1 for human (red), 2 for computer (yellow)
        self.game_over = False
        self.winner = None
        self.hover_column = -1

        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 48)

    def draw_board(self):
        """Draw the game board"""
        self.screen.fill(WHITE)

        # Draw board background
        board_rect = pygame.Rect(
            BOARD_X_OFFSET - CELL_MARGIN,
            BOARD_Y_OFFSET - CELL_MARGIN,
            BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) + CELL_MARGIN,
            BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) + CELL_MARGIN,
        )
        pygame.draw.rect(self.screen, BLUE, board_rect)

        # Draw cells and pieces
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                x = BOARD_X_OFFSET + col * (CELL_SIZE + CELL_MARGIN)
                y = BOARD_Y_OFFSET + row * (CELL_SIZE + CELL_MARGIN)

                # Draw cell background (hole)
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, BLACK, cell_rect)
                pygame.draw.circle(
                    self.screen,
                    WHITE,
                    (x + CELL_SIZE // 2, y + CELL_SIZE // 2),
                    CELL_SIZE // 2 - 2,
                )

                # Draw piece if present
                if self.board[row][col] == 1:  # Human player (red)
                    pygame.draw.circle(
                        self.screen,
                        RED,
                        (x + CELL_SIZE // 2, y + CELL_SIZE // 2),
                        CELL_SIZE // 2 - 5,
                    )
                elif self.board[row][col] == 2:  # Computer player (yellow)
                    pygame.draw.circle(
                        self.screen,
                        YELLOW,
                        (x + CELL_SIZE // 2, y + CELL_SIZE // 2),
                        CELL_SIZE // 2 - 5,
                    )

        # Draw hover effect
        if self.hover_column != -1 and not self.game_over and self.current_player == 1:
            hover_x = BOARD_X_OFFSET + self.hover_column * (CELL_SIZE + CELL_MARGIN)
            hover_y = 20
            pygame.draw.circle(
                self.screen,
                RED,
                (hover_x + CELL_SIZE // 2, hover_y + CELL_SIZE // 2),
                CELL_SIZE // 2 - 5,
            )

    def draw_ui(self):
        """Draw UI elements like current player and instructions"""
        # Current player indicator
        if not self.game_over:
            if self.current_player == 1:
                player_text = "Your Turn (Red)"
                color = RED
            else:
                player_text = "Computer's Turn (Yellow)"
                color = YELLOW
        else:
            if self.winner == 1:
                player_text = "You Win!"
                color = RED
            elif self.winner == 2:
                player_text = "Computer Wins!"
                color = YELLOW
            else:
                player_text = "It's a Tie!"
                color = GRAY

        text_surface = self.font.render(player_text, True, color)
        self.screen.blit(text_surface, (10, 10))

        # Instructions
        if not self.game_over and self.current_player == 1:
            instructions = "Click on a column to place your piece"
            inst_text = pygame.font.Font(None, 24).render(instructions, True, BLACK)
            self.screen.blit(inst_text, (10, WINDOW_HEIGHT - 30))

        # Restart button
        restart_text = "Press R to Restart"
        restart_surface = pygame.font.Font(None, 24).render(restart_text, True, BLACK)
        self.screen.blit(restart_surface, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 30))

    def get_column_from_pos(self, pos):
        """Convert mouse position to column index"""
        x, y = pos
        if BOARD_X_OFFSET <= x <= BOARD_X_OFFSET + BOARD_WIDTH * (
            CELL_SIZE + CELL_MARGIN
        ) and BOARD_Y_OFFSET <= y <= BOARD_Y_OFFSET + BOARD_HEIGHT * (
            CELL_SIZE + CELL_MARGIN
        ):
            return (x - BOARD_X_OFFSET) // (CELL_SIZE + CELL_MARGIN)
        return -1

    def is_valid_move(self, col):
        """Check if a move is valid"""
        return 0 <= col < BOARD_WIDTH and self.board[0][col] == 0

    def make_move(self, col):
        """Make a move in the specified column"""
        if not self.is_valid_move(col):
            return False

        # Find the lowest empty row in the column
        for row in range(BOARD_HEIGHT - 1, -1, -1):
            if self.board[row][col] == 0:
                self.board[row][col] = self.current_player
                return True
        return False

    def check_winner(self):
        """Check if there's a winner"""
        # Check horizontal
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH - 3):
                if (
                    self.board[row][col] != 0
                    and self.board[row][col]
                    == self.board[row][col + 1]
                    == self.board[row][col + 2]
                    == self.board[row][col + 3]
                ):
                    return self.board[row][col]

        # Check vertical
        for row in range(BOARD_HEIGHT - 3):
            for col in range(BOARD_WIDTH):
                if (
                    self.board[row][col] != 0
                    and self.board[row][col]
                    == self.board[row + 1][col]
                    == self.board[row + 2][col]
                    == self.board[row + 3][col]
                ):
                    return self.board[row][col]

        # Check diagonal (top-left to bottom-right)
        for row in range(BOARD_HEIGHT - 3):
            for col in range(BOARD_WIDTH - 3):
                if (
                    self.board[row][col] != 0
                    and self.board[row][col]
                    == self.board[row + 1][col + 1]
                    == self.board[row + 2][col + 2]
                    == self.board[row + 3][col + 3]
                ):
                    return self.board[row][col]

        # Check diagonal (top-right to bottom-left)
        for row in range(BOARD_HEIGHT - 3):
            for col in range(3, BOARD_WIDTH):
                if (
                    self.board[row][col] != 0
                    and self.board[row][col]
                    == self.board[row + 1][col - 1]
                    == self.board[row + 2][col - 2]
                    == self.board[row + 3][col - 3]
                ):
                    return self.board[row][col]

        return None

    def is_board_full(self):
        """Check if the board is full"""
        return all(self.board[0][col] != 0 for col in range(BOARD_WIDTH))

    def computer_move(self):

        # First, try to win
        for col in range(BOARD_WIDTH):
            if self.is_valid_move(col):
                # Simulate the move
                temp_board = [row[:] for row in self.board]
                for row in range(BOARD_HEIGHT - 1, -1, -1):
                    if temp_board[row][col] == 0:
                        temp_board[row][col] = 2
                        break

                # Check if this move would win
                if self.check_win_for_board(temp_board, 2):
                    return col

        # Then, try to block player
        for col in range(BOARD_WIDTH):
            if self.is_valid_move(col):
                # Simulate the move
                temp_board = [row[:] for row in self.board]
                for row in range(BOARD_HEIGHT - 1, -1, -1):
                    if temp_board[row][col] == 0:
                        temp_board[row][col] = 1
                        break

                # Check if this move would make player win
                if self.check_win_for_board(temp_board, 1):
                    return col

        # Otherwise, make a random valid move
        valid_moves = [col for col in range(BOARD_WIDTH) if self.is_valid_move(col)]
        return random.choice(valid_moves) if valid_moves else -1

    def check_win_for_board(self, board, player):
        """Check if a specific player would win on a given board state"""
        # Check horizontal
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH - 3):
                if (
                    board[row][col] == player
                    and board[row][col]
                    == board[row][col + 1]
                    == board[row][col + 2]
                    == board[row][col + 3]
                ):
                    return True

        # Check vertical
        for row in range(BOARD_HEIGHT - 3):
            for col in range(BOARD_WIDTH):
                if (
                    board[row][col] == player
                    and board[row][col]
                    == board[row + 1][col]
                    == board[row + 2][col]
                    == board[row + 3][col]
                ):
                    return True

        # Check diagonal (top-left to bottom-right)
        for row in range(BOARD_HEIGHT - 3):
            for col in range(BOARD_WIDTH - 3):
                if (
                    board[row][col] == player
                    and board[row][col]
                    == board[row + 1][col + 1]
                    == board[row + 2][col + 2]
                    == board[row + 3][col + 3]
                ):
                    return True

        # Check diagonal (top-right to bottom-left)
        for row in range(BOARD_HEIGHT - 3):
            for col in range(3, BOARD_WIDTH):
                if (
                    board[row][col] == player
                    and board[row][col]
                    == board[row + 1][col - 1]
                    == board[row + 2][col - 2]
                    == board[row + 3][col - 3]
                ):
                    return True

        return False

    def restart_game(self):
        """Restart the game"""
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.hover_column = -1

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.restart_game()

            elif event.type == pygame.MOUSEMOTION:
                if not self.game_over and self.current_player == 1:
                    self.hover_column = self.get_column_from_pos(event.pos)
                else:
                    self.hover_column = -1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    event.button == 1
                    and not self.game_over
                    and self.current_player == 1
                ):
                    col = self.get_column_from_pos(event.pos)
                    if self.make_move(col):
                        # Check for win or draw
                        winner = self.check_winner()
                        if winner:
                            self.winner = winner
                            self.game_over = True
                        elif self.is_board_full():
                            self.game_over = True
                        else:
                            self.current_player = 2  # Switch to computer

                            # Computer makes move after a short delay
                            pygame.time.wait(500)  # Small delay for better UX
                            computer_col = self.computer_move()
                            if computer_col != -1:
                                self.make_move(computer_col)
                                # Check for win or draw
                                winner = self.check_winner()
                                if winner:
                                    self.winner = winner
                                    self.game_over = True
                                elif self.is_board_full():
                                    self.game_over = True
                                else:
                                    self.current_player = 1  # Switch back to human

        return True

    def run(self):
        """Main game loop"""
        running = True
        while running:
            running = self.handle_events()

            self.draw_board()
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = ConnectFour()
    game.run()
