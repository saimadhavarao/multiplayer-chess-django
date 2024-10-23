import chess

class ChessLogic:
    def __init__(self, match=None):
        if match and match.game_state:
            self.board = chess.Board(match.game_state)
        else:
            self.board = chess.Board()
        self.match = match

    def check_is_valid(self, src, dst):
        try:
            print("src",src,dst)
            move = chess.Move.from_uci(src + dst)
            print(move)
            return move in self.board.legal_moves
        except ValueError:
            return False

    def move(self, src, dst):
        move = chess.Move.from_uci(src + dst)
        if move in self.board.legal_moves:
            self.board.push(move)
            if self.match:
                self.match.game_state = self.board.fen()
                self.match.save()
            return True
        return False

    def get_board_state(self):
        state = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                state[chess.SQUARE_NAMES[square]] = self.piece_to_unicode(piece)
        return state

    def piece_to_unicode(self, piece):
        piece_to_unicode = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }
        return piece_to_unicode.get(piece.symbol())

    def reset_board(self):
        self.board.reset()
        if self.match:
            self.match.game_state = self.board.fen()
            self.match.save()


    def is_game_over(self):
        return self.board.is_game_over()

    def get_result(self):
        return self.board.result()
