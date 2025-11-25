import random
import sys

import pygame
import pygame.gfxdraw

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
BG = (245, 247, 250)
PANEL = (250, 252, 255)
ACCENT = (20, 90, 170)  # deep blue
ACCENT_DARK = (12, 60, 120)
RED = (233, 78, 80)
YELLOW = (255, 189, 46)
HOLE = (230, 235, 240)
TEXT = (34, 44, 59)
SUBTEXT = (105, 120, 140)
SHADOW = (200, 210, 220)

FPS = 60


class Button:
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

    def draw(self, surf, font):
        # shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 6
        pygame.draw.rect(surf, SHADOW, shadow_rect, border_radius=self.radius)

        # button
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(surf, color, self.rect, border_radius=self.radius)

        # text
        txt = font.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txt_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class ConnectFour:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Connect Four")
        self.clock = pygame.time.Clock()

        # Game state
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_player = 1  # 1 = red (human), 2 = yellow (computer or P2)
        self.game_over = False
        self.winner = None
        self.winning_cells = []
        self.hover_column = -1
        self.game_mode = None  # None menu, 1=pvp,2=rand AI,3=smart AI
        self.show_menu = True

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.small_font = pygame.font.SysFont("Segoe UI", 16)

        # Buttons
        bw = 420
        bh = 64
        bx = (WINDOW_WIDTH - bw) // 2
        self.buttons = [
            Button(
                bx,
                180,
                bw,
                bh,
                "Human vs Human",
                color=(52, 152, 219),
                hover_color=(41, 128, 185),
            ),
            Button(
                bx,
                270,
                bw,
                bh,
                "Human vs Computer (Random)",
                color=(46, 204, 113),
                hover_color=(39, 174, 96),
            ),
            Button(
                bx,
                360,
                bw,
                bh,
                "Human vs Computer (Smart)",
                color=(241, 196, 15),
                hover_color=(243, 156, 18),
            ),
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

    # ----------------- Drawing helpers -----------------
    def draw_background(self):
        self.screen.fill(BG)

    def draw_menu(self):
        self.draw_background()
        title = self.title_font.render("Connect Four", True, TEXT)
        self.screen.blit(title, (60, 60))

        mouse_pos = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(mouse_pos)
            b.draw(self.screen, self.font)

    def draw_board(self):
        self.draw_background()

        # compute board px size BEFORE using the values
        board_width_px = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_height_px = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN

        # -------- Top Status Bar --------
        status_bar = pygame.Rect(BOARD_X_OFFSET - 10, 40, board_width_px + 20, 60)
        pygame.draw.rect(self.screen, PANEL, status_bar, border_radius=12)

        if not self.game_over:
            if self.current_player == 1:
                status = "Your turn — Red"
                status_col = RED
            else:
                status = "Yellow's turn"
                status_col = YELLOW
        else:
            if self.winner == 1:
                status = "Red Wins!"
                status_col = RED
            elif self.winner == 2:
                status = "Yellow Wins!"
                status_col = YELLOW
            else:
                status = "Draw"
                status_col = SUBTEXT

        status_txt = self.font.render(status, True, status_col)
        self.screen.blit(status_txt, (status_bar.x + 18, status_bar.y + 18))

        # Move Restart/Menu small buttons next to the bar
        mouse_pos = pygame.mouse.get_pos()
        self.btn_restart.rect.topleft = (status_bar.right - 340, 46)
        self.btn_menu.rect.topleft = (status_bar.right - 160, 46)

        self.btn_restart.update(mouse_pos)
        self.btn_menu.update(mouse_pos)
        self.btn_restart.draw(self.screen, self.font)
        self.btn_menu.draw(self.screen, self.font)

        # Left panel: board area with subtle shadow and rounded corners
        board_width_px = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_height_px = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_rect = pygame.Rect(
            BOARD_X_OFFSET - 12,
            BOARD_Y_OFFSET - 12,
            board_width_px + 24,
            board_height_px + 24,
        )
        pygame.draw.rect(self.screen, SHADOW, board_rect, border_radius=20)
        inner_rect = pygame.Rect(
            BOARD_X_OFFSET - 8,
            BOARD_Y_OFFSET - 8,
            board_width_px + 16,
            board_height_px + 16,
        )
        pygame.draw.rect(self.screen, ACCENT, inner_rect, border_radius=18)

        # Draw holes and pieces
        self.winning_cells = (
            self.find_winning_cells() if self.game_over and self.winner else []
        )
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                x = BOARD_X_OFFSET + col * (CELL_SIZE + CELL_MARGIN)
                y = BOARD_Y_OFFSET + row * (CELL_SIZE + CELL_MARGIN)

                # hole background
                hole_center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                radius = CELL_SIZE // 2 - 6
                # draw outer darker ring for depth
                pygame.gfxdraw.filled_circle(
                    self.screen,
                    hole_center[0],
                    hole_center[1],
                    radius + 4,
                    (18, 46, 92),
                )
                pygame.gfxdraw.filled_circle(
                    self.screen, hole_center[0], hole_center[1], radius + 2, ACCENT
                )
                pygame.gfxdraw.filled_circle(
                    self.screen, hole_center[0], hole_center[1], radius, HOLE
                )

                piece = self.board[row][col]
                if piece != 0:
                    color = RED if piece == 1 else YELLOW
                    # highlight winning pieces
                    if (row, col) in self.winning_cells:
                        glow_color = (255, 255, 255)
                        pygame.gfxdraw.filled_circle(
                            self.screen,
                            hole_center[0],
                            hole_center[1],
                            radius - 6,
                            glow_color,
                        )
                        pygame.gfxdraw.filled_circle(
                            self.screen,
                            hole_center[0],
                            hole_center[1],
                            radius - 8,
                            color,
                        )
                    else:
                        pygame.gfxdraw.filled_circle(
                            self.screen,
                            hole_center[0],
                            hole_center[1],
                            radius - 6,
                            color,
                        )
                        pygame.gfxdraw.aacircle(
                            self.screen,
                            hole_center[0],
                            hole_center[1],
                            radius - 6,
                            (30, 30, 30),
                        )

        # hover preview
        if self.hover_column != -1 and not self.game_over:
            if self.current_player == 1 or (
                self.game_mode == 1 and self.current_player == 2
            ):
                col = self.hover_column
                # find topmost empty row for preview
                for r in range(BOARD_HEIGHT):
                    if self.board[r][col] != 0:
                        preview_row = r - 1
                        break
                else:
                    preview_row = BOARD_HEIGHT - 1
                if preview_row >= 0:
                    x = BOARD_X_OFFSET + col * (CELL_SIZE + CELL_MARGIN)
                    y = BOARD_Y_OFFSET + preview_row * (CELL_SIZE + CELL_MARGIN)
                    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                    color = RED if self.current_player == 1 else YELLOW
                    # translucent
                    surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    pygame.gfxdraw.filled_circle(
                        surf,
                        CELL_SIZE // 2,
                        CELL_SIZE // 2,
                        CELL_SIZE // 2 - 10,
                        (*color, 180),
                    )
                    self.screen.blit(surf, (x, y))

        # status text
        status = ""
        if not self.game_over:
            if self.current_player == 1:
                status = "Your turn — Red"
                status_col = RED
            else:
                status = "Yellow's turn"
                status_col = YELLOW
        else:
            if self.winner == 1:
                status = "Red Wins!"
                status_col = RED
            elif self.winner == 2:
                status = "Yellow Wins!"
                status_col = YELLOW
            else:
                status = "Draw"
                status_col = SUBTEXT

        status_txt = self.font.render(status, True, status_col)

        # instructions
        inst = self.small_font.render(
            "Click a column to drop a piece. M = Menu, R = Restart", True, SUBTEXT
        )

        # big Restart/Menu buttons
        mouse_pos = pygame.mouse.get_pos()

    # ----------------- Game logic helpers -----------------
    def get_column_from_pos(self, pos):
        x, y = pos
        board_px_w = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_px_h = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        if (
            BOARD_X_OFFSET <= x <= BOARD_X_OFFSET + board_px_w
            and BOARD_Y_OFFSET <= y <= BOARD_Y_OFFSET + board_px_h
        ):
            return (x - BOARD_X_OFFSET) // (CELL_SIZE + CELL_MARGIN)
        return -1

    def is_valid_move(self, col):
        return 0 <= col < BOARD_WIDTH and self.board[0][col] == 0

    def make_move(self, col):
        if not self.is_valid_move(col):
            return False
        for row in range(BOARD_HEIGHT - 1, -1, -1):
            if self.board[row][col] == 0:
                self.board[row][col] = self.current_player
                return True
        return False

    def check_winner(self):
        # return 1 or 2 if winner else None
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
        return all(self.board[0][c] != 0 for c in range(BOARD_WIDTH))

    def computer_move(self):
        if self.game_mode == 2:
            valid = [c for c in range(BOARD_WIDTH) if self.is_valid_move(c)]
            return random.choice(valid) if valid else -1
        else:
            # smart: win -> block -> random
            for c in range(BOARD_WIDTH):
                if self.is_valid_move(c):
                    tb = [r[:] for r in self.board]
                    for r in range(BOARD_HEIGHT - 1, -1, -1):
                        if tb[r][c] == 0:
                            tb[r][c] = 2
                            break
                    if self.check_win_for_board(tb, 2):
                        return c
            for c in range(BOARD_WIDTH):
                if self.is_valid_move(c):
                    tb = [r[:] for r in self.board]
                    for r in range(BOARD_HEIGHT - 1, -1, -1):
                        if tb[r][c] == 0:
                            tb[r][c] = 1
                            break
                    if self.check_win_for_board(tb, 1):
                        return c
            valid = [c for c in range(BOARD_WIDTH) if self.is_valid_move(c)]
            return random.choice(valid) if valid else -1

    def check_win_for_board(self, board, player):
        # identical checks but for arbitrary board
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
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.winning_cells = []
        self.hover_column = -1

    def go_to_menu(self):
        self.show_menu = True
        self.game_mode = None
        self.restart_game()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.go_to_menu()
                elif event.key == pygame.K_r and self.game_over:
                    self.restart_game()
            elif event.type == pygame.MOUSEMOTION:
                if not self.show_menu:
                    if not self.game_over and (
                        self.current_player == 1
                        or (self.game_mode == 1 and self.current_player == 2)
                    ):
                        self.hover_column = self.get_column_from_pos(event.pos)
                    else:
                        self.hover_column = -1
                else:
                    for b in self.buttons:
                        b.update(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.show_menu:
                    for i, b in enumerate(self.buttons):
                        if b.is_clicked(event.pos):
                            self.game_mode = i + 1
                            self.show_menu = False
                            self.restart_game()
                else:
                    # UI buttons
                    if self.btn_restart.is_clicked(event.pos):
                        self.restart_game()
                    if self.btn_menu.is_clicked(event.pos):
                        self.go_to_menu()

                    # board clicks
                    if (
                        event.button == 1
                        and not self.game_over
                        and (
                            self.current_player == 1
                            or (self.game_mode == 1 and self.current_player == 2)
                        )
                    ):
                        col = self.get_column_from_pos(event.pos)
                        if col != -1 and self.make_move(col):
                            winner = self.check_winner()
                            if winner:
                                self.winner = winner
                                self.game_over = True
                            elif self.is_board_full():
                                self.game_over = True
                            else:
                                self.current_player = (
                                    2 if self.current_player == 1 else 1
                                )
                                # computer move
                                if (
                                    self.game_mode != 1
                                    and not self.game_over
                                    and self.current_player == 2
                                ):
                                    pygame.time.wait(350)
                                    c = self.computer_move()
                                    if c != -1:
                                        self.make_move(c)
                                        winner = self.check_winner()
                                        if winner:
                                            self.winner = winner
                                            self.game_over = True
                                        elif self.is_board_full():
                                            self.game_over = True
                                        else:
                                            self.current_player = 1
        return True

    def get_column_from_pos(self, pos):
        x, y = pos
        board_px_w = BOARD_WIDTH * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        board_px_h = BOARD_HEIGHT * (CELL_SIZE + CELL_MARGIN) - CELL_MARGIN
        if (
            BOARD_X_OFFSET <= x <= BOARD_X_OFFSET + board_px_w
            and BOARD_Y_OFFSET <= y <= BOARD_Y_OFFSET + board_px_h
        ):
            return int((x - BOARD_X_OFFSET) // (CELL_SIZE + CELL_MARGIN))
        return -1

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            if self.show_menu:
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
