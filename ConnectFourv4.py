import random
import sys
import numpy as np
import pygame
import pygame.gfxdraw
import math

# To run: pip install pygame
# python3 ConnectFour.py


pygame.init()

# Constants
WINDOW_WIDTH = 880
WINDOW_HEIGHT = 700
BOARD_WIDTH = 7
BOARD_HEIGHT = 6
CELL_SIZE = 84
CELL_MARGIN = 8
BOARD_X_OFFSET = 120
BOARD_Y_OFFSET = 120

# Colors (modern palette)
BG_TOP = (245, 247, 250)
BG_BOTTOM = (220, 225, 235)
PANEL = (250, 252, 255)
ACCENT = (20, 90, 170)  # deep blue
ACCENT_DARK = (12, 60, 120)
RED = (233, 78, 80)
YELLOW = (255, 189, 46)
HOLE = (230, 235, 240)
TEXT = (34, 44, 59)
SUBTEXT = (105, 120, 140)
SHADOW = (0, 0, 0, 40)  # Alpha shadow

FPS = 60

# Game Phases
PHASE_MENU = 0
PHASE_PLAYER_TURN = 1
PHASE_AI_THINKING = 2
PHASE_ANIMATING = 3
PHASE_GAME_OVER = 4

# AI difficulty levels
CENTER_PREFERENCE = {3: 0.3, 2: 0.15, 1: 0.1, 4: 0.2, 5: 0.2, 0: 0.1, 6: 0.1}


class Button:
    """Interactive button with hover effects and visual feedback."""
    def __init__(
        self, x, y, w, h, text, color=ACCENT, hover_color=ACCENT_DARK, radius=12
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.base_color = color
        self.hover_color = hover_color
        self.radius = radius
        self.is_hovered = False
        self.scale = 1.0
        self.target_scale = 1.0

    def draw(self, surf, font):
        """Draw button with shadow and hover state."""
        # animate scale
        self.scale += (self.target_scale - self.scale) * 0.2
        
        # scale rect for drawing
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        cx, cy = self.rect.center
        draw_rect = pygame.Rect(0, 0, w, h)
        draw_rect.center = (cx, cy)

        # shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 4
        s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, SHADOW, s_surf.get_rect(), border_radius=self.radius)
        surf.blit(s_surf, shadow_rect)

        # button
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(surf, color, draw_rect, border_radius=self.radius)

        # text
        txt = font.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=draw_rect.center)
        surf.blit(txt, txt_rect)

    def update(self, mouse_pos):
        """Update hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.target_scale = 1.05 if self.is_hovered else 1.0

    def is_clicked(self, mouse_pos):
        """Check if button was clicked."""
        return self.rect.collidepoint(mouse_pos)


class ConnectFour:
    """Main game controller for Connect Four gameplay and rendering."""
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Connect Four")
        self.clock = pygame.time.Clock()

        # Game state
        flipped_board = np.zeros((BOARD_HEIGHT,BOARD_WIDTH))
        self.minimax_board = np.flip(flipped_board)
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_player = 1  # 1 = red (human), 2 = yellow (computer or P2)
        self.winner = None
        self.winning_cells = []
        self.hover_column = -1
        self.game_mode = None  # None=menu, 1=pvp, 2=rand AI, 3=smart AI
        self.phase = PHASE_MENU
        
        # Animation state
        self.anim_piece = None # {col, row, y, target_y, player, velocity}
        self.ai_timer = 0

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 56, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 22)
        self.small_font = pygame.font.SysFont("Segoe UI", 16)

        # Buttons
        bw = 420
        bh = 70
        bx = (WINDOW_WIDTH - bw) // 2
        self.buttons = [
            Button(
                bx,
                220,
                bw,
                bh,
                "Human vs Human",
                color=(52, 152, 219),
                hover_color=(41, 128, 185),
            ),
            Button(
                bx,
                310,
                bw,
                bh,
                "Human vs Computer (Random)",
                color=(46, 204, 113),
                hover_color=(39, 174, 96),
            ),
            Button(
                bx,
                400,
                bw,
                bh,
                "Human vs Computer (Smart)",
                color=(241, 196, 15),
                hover_color=(243, 156, 18),
            ),
            Button(
                bx,
                490,
                bw,
                bh,
                "Human vs Computer (MinMax)",
                color=(241, 196, 15),
                hover_color=(243, 156, 18),
            )
        ]

        # Small UI buttons
        self.btn_restart = Button(
            WINDOW_WIDTH - 180,
            40,
            160,
            44,
            "Restart",
            color=(90, 90, 110),
            hover_color=(60, 60, 80),
            radius=10,
        )
        self.btn_menu = Button(
            WINDOW_WIDTH - 360,
            40,
            160,
            44,
            "Menu",
            color=(90, 90, 110),
            hover_color=(60, 60, 80),
            radius=10,
        )

    # ===== DRAWING METHODS =====
    def draw_background(self):
        """Fill screen with gradient background."""
        # Vertical gradient using rects (faster)
        step = 2
        for y in range(0, WINDOW_HEIGHT, step):
            alpha = y / WINDOW_HEIGHT
            r = int(BG_TOP[0] * (1 - alpha) + BG_BOTTOM[0] * alpha)
            g = int(BG_TOP[1] * (1 - alpha) + BG_BOTTOM[1] * alpha)
            b = int(BG_TOP[2] * (1 - alpha) + BG_BOTTOM[2] * alpha)
            pygame.draw.rect(self.screen, (r,g,b), (0, y, WINDOW_WIDTH, step))

    def draw_menu(self):
        """Render main menu with game mode selection."""
        self.draw_background()
        
        # Decorative circles
        pygame.gfxdraw.filled_circle(self.screen, 100, 100, 40, (*RED, 100))
        pygame.gfxdraw.filled_circle(self.screen, WINDOW_WIDTH-80, WINDOW_HEIGHT-80, 60, (*YELLOW, 100))
        
        # Title with shadow
        title_txt = "Connect Four"
        title_surf = self.title_font.render(title_txt, True, TEXT)
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 120))
        
        # Shadow
        s_surf = self.title_font.render(title_txt, True, (0,0,0))
        s_surf.set_alpha(30)
        self.screen.blit(s_surf, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(mouse_pos)
            b.draw(self.screen, self.font)

    def draw_board(self):
        """Render game board with pieces and UI elements."""
        self.draw_background()

        # compute board px size
        board_width_px = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_height_px = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN

        # -------- Top Status Bar --------
        status_bar = pygame.Rect(BOARD_X_OFFSET - 10, 40, board_width_px + 20, 60)
        pygame.draw.rect(self.screen, PANEL, status_bar, border_radius=12)
        
        # Status Text
        status = ""
        status_col = TEXT
        
        if self.phase == PHASE_GAME_OVER:
            if self.winner == 1:
                status = "Red Wins!"
                status_col = RED
            elif self.winner == 2:
                status = "Yellow Wins!"
                status_col = YELLOW
            else:
                status = "Draw!"
                status_col = SUBTEXT
        elif self.phase == PHASE_AI_THINKING:
            status = "Computer is thinking..."
        else:
            if self.current_player == 1:
                status = "Your Turn (Red)"
                status_col = RED
            else:
                status = "Yellow's Turn"
                status_col = YELLOW

        status_txt = self.font.render(status, True, status_col)
        self.screen.blit(status_txt, (status_bar.x + 24, status_bar.y + 16))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        self.btn_restart.rect.topleft = (status_bar.right - 340, 46)
        self.btn_menu.rect.topleft = (status_bar.right - 160, 46)

        self.btn_restart.update(mouse_pos)
        self.btn_menu.update(mouse_pos)
        self.btn_restart.draw(self.screen, self.font)
        self.btn_menu.draw(self.screen, self.font)

        # Board Background
        board_rect = pygame.Rect(
            BOARD_X_OFFSET - 12,
            BOARD_Y_OFFSET - 12,
            board_width_px + 24,
            board_height_px + 24,
        )
        
        # Board Shadow
        shadow_rect = board_rect.copy()
        shadow_rect.y += 8
        s_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, SHADOW, s_surf.get_rect(), border_radius=20)
        self.screen.blit(s_surf, shadow_rect)

        # Board Body
        pygame.draw.rect(self.screen, ACCENT, board_rect, border_radius=20)
        
        # Highlight
        pygame.draw.rect(self.screen, (255,255,255,30), board_rect, width=2, border_radius=20)

        # Draw Cells
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                x = BOARD_X_OFFSET + col * (CELL_SIZE + CELL_MARGIN)
                y = BOARD_Y_OFFSET + row * (CELL_SIZE + CELL_MARGIN)
                center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                radius = CELL_SIZE // 2 - 6

                # Hole background (darker blue/shadow)
                pygame.gfxdraw.filled_circle(self.screen, center[0], center[1], radius + 2, (10, 50, 100))
                pygame.gfxdraw.aacircle(self.screen, center[0], center[1], radius + 2, (10, 50, 100))
                
                # Determine what to draw in the hole
                piece_val = self.board[row][col]
                
                # Skip drawing if this is the destination of the currently animating piece
                if self.anim_piece and self.anim_piece['row'] == row and self.anim_piece['col'] == col:
                    piece_val = 0 # Treat as empty for drawing, we draw the moving one separately
                
                if piece_val == 0:
                    # Empty hole
                    pygame.gfxdraw.filled_circle(self.screen, center[0], center[1], radius, HOLE)
                else:
                    # Static piece
                    color = RED if piece_val == 1 else YELLOW
                    self._draw_piece(center[0], center[1], radius, color)
                    
                    # Winner glow
                    if self.phase == PHASE_GAME_OVER and (row, col) in self.winning_cells:
                        pygame.gfxdraw.filled_circle(self.screen, center[0], center[1], radius, (255, 255, 255, 100))
                        pygame.draw.circle(self.screen, (255, 255, 255), center, radius, 4)

        # Draw Animating Piece
        if self.anim_piece:
            ap = self.anim_piece
            x = BOARD_X_OFFSET + ap['col'] * (CELL_SIZE + CELL_MARGIN) + CELL_SIZE // 2
            y = int(ap['y']) + CELL_SIZE // 2
            color = RED if ap['player'] == 1 else YELLOW
            radius = CELL_SIZE // 2 - 6
            
            # Clip drawing to board area (optional, but good for polish if piece starts high)
            self._draw_piece(x, y, radius, color)

        # Draw Hover Preview
        if self.phase == PHASE_PLAYER_TURN and self.hover_column != -1:
            col = self.hover_column
            # Find landing row
            landing_row = -1
            for r in range(BOARD_HEIGHT - 1, -1, -1):
                if self.board[r][col] == 0:
                    landing_row = r
                    break
            
            if landing_row != -1:
                x = BOARD_X_OFFSET + col * (CELL_SIZE + CELL_MARGIN)
                y = BOARD_Y_OFFSET + landing_row * (CELL_SIZE + CELL_MARGIN)
                center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                radius = CELL_SIZE // 2 - 6
                
                color = RED if self.current_player == 1 else YELLOW
                
                # Semi-transparent ghost
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.gfxdraw.filled_circle(s, CELL_SIZE//2, CELL_SIZE//2, radius, (*color, 100))
                self.screen.blit(s, (x, y))

    def _draw_piece(self, x, y, radius, color):
        """Helper to draw a styled piece."""
        # Main body
        pygame.gfxdraw.filled_circle(self.screen, x, y, radius, color)
        pygame.gfxdraw.aacircle(self.screen, x, y, radius, color)
        
        # Inner detail (bevel/shine)
        highlight = (255, 255, 255, 80)
        shadow = (0, 0, 0, 50)
        
        # Top-left highlight
        pygame.gfxdraw.filled_circle(self.screen, x - 5, y - 5, radius - 10, highlight)
        # Bottom-right shadow overlay (simulated by drawing smaller circle offset or arc? 
        # simple way: smaller circle)
        
        # inner rim
        pygame.draw.circle(self.screen, (0,0,0,30), (x,y), radius, 2)

    # ===== LOGIC & ANIMATION =====

    """Minimax implementation"""

    #Scoring function
    def evaluate_window(self,window, piece):
        score = 0
        opp_piece = 1 if piece == 2 else 2


        if window.count(piece) == 4:
            score += 100
            
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4
        

        return score
    
    
    def minimax(self,board,depth, alpha, beta, maximizingPlayer):
        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board)
        if depth == 0 or is_terminal:
            if is_terminal:
                    
                if self.check_win_for_board(board, 2):
                    return (None, 1000)
                elif self.check_win_for_board(board, 1):
                    return (None, -1000)
                else:
                    return (None,0)
            else:
                return (None, self.score_position(board, 2))
        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                board_copy = board.copy()
                self.drop_piece(board_copy, row, col, 2)
                new_score = self.minimax(board_copy, depth-1, alpha, beta, False)[1]

                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(value, alpha)
                if alpha >= beta:
                    break

            return column, value
        else:
            value= math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                board_copy = board.copy()
                self.drop_piece(board_copy, row, col, 1)
                new_score = self.minimax(board_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                if alpha >= beta:
                    break
            return column, value



    def is_terminal_node(self,board):
        return self.check_win_for_board(board, 1) or self.check_win_for_board(board, 2) or len(self.get_valid_locations(board)) == 0
       

    def is_valid_location(self, board, col):
        return board[0][col] == 0

    
    def drop_piece(self, board, row, col, piece):
        board[row][col] = piece


    def score_position(self, board, piece):
        score = 0


        #Score center column

       
        center_array = [int(i) for i in list(board[:, BOARD_WIDTH//2])]
        center_count = center_array.count(piece)
        score += center_count * 3

         #Horizontal scoring
        for r in range(BOARD_HEIGHT):
            row_array = [int(i) for i in list(board[r,:])]
            for c in range(BOARD_WIDTH-3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece)
                
        #Score verticle
        for c in range(BOARD_WIDTH):
            col_array = [int(i) for i in list(board[:,c])]

            for r in range(BOARD_HEIGHT-3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)
        #Score diagonal
        for r in range(BOARD_HEIGHT-3):
            for c in range(BOARD_WIDTH-3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)
        for r in range(BOARD_HEIGHT-3):
            for c in range(BOARD_WIDTH-3):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        
        return score
    

    def pick_best_move(self, board, piece):
        valid_locations = self.get_valid_locations(board)
        best_score = -10000
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            row = self.get_next_open_row(board, col)
            temp_board = board.copy()
            self.drop_piece(temp_board, row, col, piece)
            score = self.score_position(temp_board, piece)

            if score > best_score:
               # print(score, best_score)
                best_score = score
                best_col = col
        print(self.minimax_board)
        return best_col





    def get_valid_locations(self, board):
        valid_location = []
        for col in range (BOARD_WIDTH):
            if self.is_valid_location(board, col):
                valid_location.append(col)
        print(valid_location)
        return valid_location
    def get_next_open_row(self,board, col):
        for r in range(BOARD_HEIGHT-1,-1,-1):
            if board[r][col] == 0:
                return r


    

    """End of MiniMax"""
                    
                
        












    def start_move_animation(self, col, player):
        """Initialize animation for a move."""
        # Find target row
        row = -1
        for r in range(BOARD_HEIGHT - 1, -1, -1):
            if self.board[r][col] == 0:
                row = r
                break
        
        if row == -1:
            return False # Invalid
            
        target_y = BOARD_Y_OFFSET + row * (CELL_SIZE + CELL_MARGIN)
        start_y = BOARD_Y_OFFSET - CELL_SIZE - 20
        
        self.anim_piece = {
            'col': col,
            'row': row,
            'player': player,
            'y': start_y,
            'target_y': target_y,
            'velocity': 0
        }
        self.phase = PHASE_ANIMATING
        return True

    def update_animation(self):
        """Advance animation frame."""
        if not self.anim_piece:
            self.phase = PHASE_PLAYER_TURN # Recovery
            return

        # Gravity physics
        gravity = 2.0
        self.anim_piece['velocity'] += gravity
        self.anim_piece['y'] += self.anim_piece['velocity']
        
        # Bounce or Stop logic
        if self.anim_piece['y'] >= self.anim_piece['target_y']:
            self.anim_piece['y'] = self.anim_piece['target_y']
            # Bounce effect?
            if self.anim_piece['velocity'] > 15:
                 self.anim_piece['velocity'] = -self.anim_piece['velocity'] * 0.3
            else:
                # Done
                self.finalize_move()

    def finalize_move(self):
        """Commit move to board and check game state."""
        if not self.anim_piece:
            return

        r, c = self.anim_piece['row'], self.anim_piece['col']
        p = self.anim_piece['player']
        self.board[r][c] = p
        self.minimax_board[r][c] = p
        self.anim_piece = None

        # Check win
        winner = self.check_winner()
        if winner:
            self.winner = winner
            self.phase = PHASE_GAME_OVER
            self.winning_cells = self.find_winning_cells()
            return
            
        if self.is_board_full():
            self.phase = PHASE_GAME_OVER
            return

        # Switch turn
        self.current_player = 2 if self.current_player == 1 else 1
        
        # Determine next phase
        if self.game_mode == 1:
            self.phase = PHASE_PLAYER_TURN
        else:
            if self.current_player == 2:
                self.phase = PHASE_AI_THINKING
                self.ai_timer = pygame.time.get_ticks() + 500 # 500ms think time
            else:
                self.phase = PHASE_PLAYER_TURN

    def update(self):
        """General update loop."""
        if self.phase == PHASE_ANIMATING:
            self.update_animation()
        elif self.phase == PHASE_AI_THINKING:
            if pygame.time.get_ticks() >= self.ai_timer:
                col = self.computer_move()
                if col != -1:
                    self.start_move_animation(col, 2)
                else:
                    # No moves? Draw/Over
                    self.phase = PHASE_GAME_OVER

    # ===== GAME LOGIC METHODS =====
    # ... (Keep helper methods) ...


    def get_column_from_pos(self, pos):
        """Convert mouse position to board column index."""
        x, y = pos
        board_px_w = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_px_h = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        if (
            BOARD_X_OFFSET <= x <= BOARD_X_OFFSET + board_px_w
            and BOARD_Y_OFFSET <= y <= BOARD_Y_OFFSET + board_px_h
        ):
            return int((x - BOARD_X_OFFSET) // (CELL_SIZE + CELL_MARGIN))
        return -1

    def is_valid_move(self, col):
        """Check if column has space for a new piece."""
        return 0 <= col < BOARD_WIDTH and self.board[0][col] == 0

    def make_move(self, col):
        """Place piece in column; returns True if successful."""
        if not self.is_valid_move(col):
            return False
        for row in range(BOARD_HEIGHT - 1, -1, -1):
            if self.board[row][col] == 0:
                self.board[row][col] = self.current_player
                return True
        return False

    def check_winner(self):
        """Check all directions for 4 in a row; returns player ID or None."""
        # horizontal
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH - 3):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r][c + 1]
                    == self.board[r][c + 2]
                    == self.board[r][c + 3]
                ):
                    return v
        # vertical
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c]
                    == self.board[r + 2][c]
                    == self.board[r + 3][c]
                ):
                    return v
        # diag TL-BR
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH - 3):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c + 1]
                    == self.board[r + 2][c + 2]
                    == self.board[r + 3][c + 3]
                ):
                    return v
        # diag TR-BL
        for r in range(BOARD_HEIGHT - 3):
            for c in range(3, BOARD_WIDTH):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c - 1]
                    == self.board[r + 2][c - 2]
                    == self.board[r + 3][c - 3]
                ):
                    return v
        return None

    def find_winning_cells(self):
        """Locate the 4 cells that form the winning line."""
        cells = []
        # horizontal
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH - 3):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r][c + 1]
                    == self.board[r][c + 2]
                    == self.board[r][c + 3]
                ):
                    cells = [(r, c + i) for i in range(4)]
                    return cells
        # vertical
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c]
                    == self.board[r + 2][c]
                    == self.board[r + 3][c]
                ):
                    cells = [(r + i, c) for i in range(4)]
                    return cells
        # diag TL-BR
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH - 3):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c + 1]
                    == self.board[r + 2][c + 2]
                    == self.board[r + 3][c + 3]
                ):
                    cells = [(r + i, c + i) for i in range(4)]
                    return cells
        # diag TR-BL
        for r in range(BOARD_HEIGHT - 3):
            for c in range(3, BOARD_WIDTH):
                v = self.board[r][c]
                if (
                    v != 0
                    and v
                    == self.board[r + 1][c - 1]
                    == self.board[r + 2][c - 2]
                    == self.board[r + 3][c - 3]
                ):
                    cells = [(r + i, c - i) for i in range(4)]
                    return cells
        return cells

    def is_board_full(self):
        """Check if board has no empty cells."""
        return all(self.board[0][c] != 0 for c in range(BOARD_WIDTH))

    def computer_move(self):
        """Return best computer move based on difficulty level."""
        if self.game_mode == 2:
            # Random mode: prefer center with slight weighting
            return self._random_move()
        elif self.game_mode == 4:
            return self.minimax(self.minimax_board,3, -math.inf, math.inf,True)[0]
        else:
            # Smart mode: win, block, prefer center, avoid opponent threats
            return self._smart_move()

    def _random_move(self):
        """Random AI with center column preference."""
        valid = [c for c in range(BOARD_WIDTH) if self.is_valid_move(c)]
        if not valid:
            return -1
        # Prefer center columns with weighted randomness
        weighted = [(c, CENTER_PREFERENCE.get(c, 0.1)) for c in valid]
        total = sum(w[1] for w in weighted)
        if total > 0:
            rand_val = random.random() * total
            cumulative = 0
            for col, weight in weighted:
                cumulative += weight
                if rand_val <= cumulative:
                    return col
        return random.choice(valid)

    def _smart_move(self):
        """Smart AI: win, block, create threats, prefer center."""
        # Priority 1: Win immediately
        for c in range(BOARD_WIDTH):
            if self.is_valid_move(c):
                if self._would_win(c, 2):
                    return c
        
        # Priority 2: Block opponent win
        for c in range(BOARD_WIDTH):
            if self.is_valid_move(c):
                if self._would_win(c, 1):
                    return c
                    
        # Priority 3: Create threat (2 in a row with potential for 3), but ensure safety
        threat_cols = []
        for c in range(BOARD_WIDTH):
            if self.is_valid_move(c):
                if self._count_consecutive(c, 2) >= 2 and not self._creates_opponent_threat(c):
                    threat_cols.append(c)
        if threat_cols:
            return self._prefer_center(threat_cols)
            
        # Priority 4: Avoid giving opponent easy wins, prefer center
        safe_cols = []
        for c in range(BOARD_WIDTH):
            if self.is_valid_move(c):
                if not self._creates_opponent_threat(c):
                    safe_cols.append(c)
        if safe_cols:
            return self._prefer_center(safe_cols)
            
        # Fallback: prefer center among valid moves (even if unsafe, since we must move)
        valid = [c for c in range(BOARD_WIDTH) if self.is_valid_move(c)]
        return self._prefer_center(valid) if valid else -1

    def _would_win(self, col, player):
        """Check if move in column would result in a win for player."""
        tb = [r[:] for r in self.board]
        for r in range(BOARD_HEIGHT - 1, -1, -1):
            if tb[r][col] == 0:
                tb[r][col] = player
                break
        return self.check_win_for_board(tb, player)

    def _count_consecutive(self, col, player):
        """Count max consecutive pieces of player near a potential move."""
        tb = [r[:] for r in self.board]
        for r in range(BOARD_HEIGHT - 1, -1, -1):
            if tb[r][col] == 0:
                tb[r][col] = player
                break
        # Find max consecutive from this position
        max_count = 0
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                if tb[r][c] == player:
                    # Check all 4 directions
                    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                        count = 1
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < BOARD_HEIGHT and 0 <= nc < BOARD_WIDTH and tb[nr][nc] == player:
                            count += 1
                            nr += dr
                            nc += dc
                        max_count = max(max_count, count)
        return max_count

    def _creates_opponent_threat(self, col):
        """Check if placing a piece here allows the opponent to win on the very next move (above)."""
        # Find where our piece would land
        target_row = -1
        for r in range(BOARD_HEIGHT - 1, -1, -1):
            if self.board[r][col] == 0:
                target_row = r
                break
        
        if target_row == -1:
            return False # Should not happen if is_valid_move checked
            
        # If we place at target_row, the cell above (target_row - 1) becomes available.
        # Check if opponent playing at (target_row - 1) would win.
        if target_row > 0:
            # Simulate our move first
            self.board[target_row][col] = 2
            
            # Check opponent win at target_row - 1
            would_loss = self._would_win_on_board_at(target_row - 1, col, 1)
            
            # Undo our move
            self.board[target_row][col] = 0
            
            return would_loss
            
        return False

    def _would_win_on_board_at(self, row, col, player):
        """Check if placing a piece at (row, col) wins for player on current board."""
        # Temporarily place piece
        self.board[row][col] = player
        is_win = self.check_win_for_board(self.board, player)
        self.board[row][col] = 0
        return is_win

    def _prefer_center(self, cols):
        """Choose column closest to center from list."""
        center = BOARD_WIDTH // 2
        return min(cols, key=lambda c: abs(c - center))

    def check_win_for_board(self, board, player):
        """Check if player won on given board state."""
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH - 3):
                if (
                    board[r][c] == player
                    and board[r][c + 1] == player
                    and board[r][c + 2] == player
                    and board[r][c + 3] == player
                ):
                    return True
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH):
                if (
                    board[r][c] == player
                    and board[r + 1][c] == player
                    and board[r + 2][c] == player
                    and board[r + 3][c] == player
                ):
                    return True
        for r in range(BOARD_HEIGHT - 3):
            for c in range(BOARD_WIDTH - 3):
                if (
                    board[r][c] == player
                    and board[r + 1][c + 1] == player
                    and board[r + 2][c + 2] == player
                    and board[r + 3][c + 3] == player
                ):
                    return True
        for r in range(BOARD_HEIGHT - 3):
            for c in range(3, BOARD_WIDTH):
                if (
                    board[r][c] == player
                    and board[r + 1][c - 1] == player
                    and board[r + 2][c - 2] == player
                    and board[r + 3][c - 3] == player
                ):
                    return True
        return False

    def restart_game(self):
        """Reset board and game state for new game."""
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        flipped_board = np.zeros((BOARD_HEIGHT,BOARD_WIDTH))
        self.minimax_board = np.flip(flipped_board)
        self.current_player = 1
        self.winner = None
        self.winning_cells = []
        self.hover_column = -1
        self.anim_piece = None
        self.ai_timer = 0
        
        if self.game_mode is None:
            self.phase = PHASE_MENU
        else:
            self.phase = PHASE_PLAYER_TURN

    def go_to_menu(self):
        """Return to main menu."""
        self.game_mode = None
        self.phase = PHASE_MENU
        self.restart_game()

    # ===== EVENT HANDLING =====
    def handle_events(self):
        """Process user input and game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.go_to_menu()
                elif event.key == pygame.K_r and self.phase == PHASE_GAME_OVER:
                    self.restart_game()
            
            elif event.type == pygame.MOUSEMOTION:
                if self.phase == PHASE_MENU:
                    for b in self.buttons:
                        b.update(event.pos)
                else:
                    if self.phase == PHASE_PLAYER_TURN:
                        self.hover_column = self.get_column_from_pos(event.pos)
                    else:
                        self.hover_column = -1
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.phase == PHASE_MENU:
                    for i, b in enumerate(self.buttons):
                        if b.is_clicked(event.pos):
                            self.game_mode = i + 1
                            self.restart_game()
                else:
                    # UI buttons
                    if self.btn_restart.is_clicked(event.pos):
                        self.restart_game()
                    if self.btn_menu.is_clicked(event.pos):
                        self.go_to_menu()

                    # board clicks
                    if event.button == 1 and self.phase == PHASE_PLAYER_TURN:
                        col = self.get_column_from_pos(event.pos)
                        if col != -1:
                            # Try to start move
                            self.start_move_animation(col, self.current_player)
                            
        return True

    def run(self):
        """Main game loop."""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            
            if self.phase == PHASE_MENU:
                self.draw_menu()
            else:
                self.draw_board()
                
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = ConnectFour()
    game.run()
