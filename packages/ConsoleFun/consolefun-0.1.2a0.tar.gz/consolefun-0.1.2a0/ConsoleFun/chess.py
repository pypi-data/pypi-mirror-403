import pyfiglet

WHITE = "white"
BLACK = "black"


class Piece:
    def __init__(self, color):
        self.color = color

    def symbol(self):
        return "?"

    def moves(self, board, x, y):
        return []


class King(Piece):
    def symbol(self):
        return "K" if self.color == WHITE else "k"

    def moves(self, board, x, y):
        dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        moves = []
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] is None or board[nx][ny].color != self.color:
                    moves.append((nx, ny))
        return moves


class Queen(Piece):
    def symbol(self):
        return "Q" if self.color == WHITE else "q"

    def moves(self, board, x, y):
        return rook_moves(board, x, y, self.color) + bishop_moves(board, x, y, self.color)


class Rook(Piece):
    def symbol(self):
        return "R" if self.color == WHITE else "r"

    def moves(self, board, x, y):
        return rook_moves(board, x, y, self.color)


class Bishop(Piece):
    def symbol(self):
        return "B" if self.color == WHITE else "b"

    def moves(self, board, x, y):
        return bishop_moves(board, x, y, self.color)


class Knight(Piece):
    def symbol(self):
        return "N" if self.color == WHITE else "n"

    def moves(self, board, x, y):
        steps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        moves = []
        for dx, dy in steps:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] is None or board[nx][ny].color != self.color:
                    moves.append((nx, ny))
        return moves


class Pawn(Piece):
    def symbol(self):
        return "P" if self.color == WHITE else "p"

    def moves(self, board, x, y):
        moves = []
        direction = -1 if self.color == WHITE else 1
        start_row = 6 if self.color == WHITE else 1

        # forward move
        if board[x + direction][y] is None:
            moves.append((x + direction, y))
            if x == start_row and board[x + 2 * direction][y] is None:
                moves.append((x + 2 * direction, y))

        # captures
        for dy in [-1, 1]:
            nx, ny = x + direction, y + dy
            if 0 <= ny < 8 and 0 <= nx < 8:
                if board[nx][ny] and board[nx][ny].color != self.color:
                    moves.append((nx, ny))

        return moves


def rook_moves(board, x, y, color):
    moves = []
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in dirs:
        nx, ny = x, y
        while True:
            nx += dx
            ny += dy
            if not (0 <= nx < 8 and 0 <= ny < 8):
                break
            if board[nx][ny] is None:
                moves.append((nx, ny))
            else:
                if board[nx][ny].color != color:
                    moves.append((nx, ny))
                break
    return moves


def bishop_moves(board, x, y, color):
    moves = []
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dx, dy in dirs:
        nx, ny = x, y
        while True:
            nx += dx
            ny += dy
            if not (0 <= nx < 8 and 0 <= ny < 8):
                break
            if board[nx][ny] is None:
                moves.append((nx, ny))
            else:
                if board[nx][ny].color != color:
                    moves.append((nx, ny))
                break
    return moves


class ChessGame:
    def __init__(self):
        self.board = [[None] * 8 for _ in range(8)]
        self.turn = WHITE
        self.setup_board()

    def setup_board(self):
        for i in range(8):
            self.board[6][i] = Pawn(WHITE)
            self.board[1][i] = Pawn(BLACK)

        pieces = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i, p in enumerate(pieces):
            self.board[7][i] = p(WHITE)
            self.board[0][i] = p(BLACK)

    def print_board(self):
        print("\n  a b c d e f g h")
        for i in range(8):
            print(8 - i, end=" ")
            for j in range(8):
                piece = self.board[i][j]
                print(piece.symbol() if piece else ".", end=" ")
            print(8 - i)
        print("  a b c d e f g h\n")

    def parse_move(self, move):
        if len(move) != 4:
            return None
        y1 = ord(move[0]) - ord('a')
        x1 = 8 - int(move[1])
        y2 = ord(move[2]) - ord('a')
        x2 = 8 - int(move[3])
        return x1, y1, x2, y2

    def move_piece(self, x1, y1, x2, y2):
        piece = self.board[x1][y1]
        if not piece or piece.color != self.turn:
            return False

        if (x2, y2) not in piece.moves(self.board, x1, y1):
            return False

        self.board[x2][y2] = piece
        self.board[x1][y1] = None
        self.turn = BLACK if self.turn == WHITE else WHITE
        return True

    def start(self):
        while True:
            self.print_board()
            print(f"{self.turn.upper()} to move (e2e4 format, 'quit' to exit):")
            move = input("> ")
            if move == "quit":
                break
            parsed = self.parse_move(move)
            if not parsed or not self.move_piece(*parsed):
                print("Invalid move!")


def play():
    print(pyfiglet.figlet_format("CONSOLE GAMES"))

    game = ChessGame()
    game.start()
