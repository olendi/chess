import logging
import copy

logging.basicConfig(level=logging.DEBUG)

# colors
WHITE, BLACK = 'w', 'b'

# pieces
KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN = 'k', 'q', 'r', 'b', 'n', 'p'

def validate_name(name):
    if name not in (KING, QUEEN, ROOK, KNIGHT, BISHOP, PAWN):
        raise Exception, "Piece name {} is not allowed".format(name)

def validate_color(color):
    if color not in (WHITE, BLACK):
        raise Exception, "Color name {} is not allowed".format(color)

def c2n(x,y):
    return chr(ord('A')+x) + chr(ord('1')+y)

class Piece(object):
    
    def __init__(self, name, color):
        validate_name(name)
        validate_color(color)

        self.name = name
        self.color = color
        self.symbol = name if name != PAWN else ''

    def __repr__(self):
        return "{}".format(self.name if self.color == BLACK else self.name.upper())

class Board(object):
    def __init__(self):
        self.board = [[None for j in range(8)] for i in range(8)]

        # kingside and queenside castles availability
        self.castles_available = { WHITE : { KING : True, QUEEN : True },
                                  BLACK : { KING : True, QUEEN : True } }

        self.en_passant_target = None
        self.half_move_clock = 0
        self.full_move_number = 1

        ## SET UP THE PIECES
        for color in (WHITE, BLACK):
            # move_direction and back_rank functions depend on the active_color variable
            # so we set it here to the color whose pieces we are setting up
            self.active_color = color
            direction = self.move_direction()
            back_rank = self.back_rank()

            # setting up the pieces in the back rank
            for i, piece in enumerate( (ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT,ROOK) ):
                self.board[i][back_rank] = Piece(piece, color)

            # pawns rank
            for i in range(8):
                self.board[i][back_rank+direction] = Piece(PAWN, color)

        # now setting the active_color for beginning of the game
        self.active_color = WHITE

        logging.debug("Finished board setup")

    def __repr__(self):
        sep = "---------------------------------------"
        output  = ["   | A | B | C | D | E | F | G | H |   "]
        output.append(sep)
        for i in range(8):
            line = " {} |".format(i+1)
            for j in range(8):
                piece = self.board[j][i]
                line += " {} |".format(' ' if piece is None else str(piece))
            line += "   "
            output.append(line)
            output.append(sep)
        output.append("   |   |   |   |   |   |   |   |   |   ")
        output.reverse()
        output.append("TURN: {}".format(self.active_color))
        output.append("CASTLES: {}".format(self.castles_available))
        output.append("En Passant Target: {}".format(self.en_passant_target))
        output.append("Move Number: {}".format(self.full_move_number))
        output.append("Half Move Clock (50 Move Rule): {}".format(self.half_move_clock))
        
        return "\n".join(output)

    def flip_active_color(self):
        self.active_color = BLACK if self.active_color == WHITE else WHITE

    # get a piece given its x and y coordinates
    def get_piece(self, x, y):
        return self.board[x][y]

    # this provides the direction of movement for the current active side
    # white moves up (+1) while black moves down (-1)
    def move_direction(self):
        return 1 if self.active_color == WHITE else -1

    # this provides the back rank for the current active side's king
    # for white this is 0 and for black this is 7
    def back_rank(self):
        return 0 if self.active_color == WHITE else 7

    # pawn_capture is a ternary/tristate variable
    # a value of None means this is not for a panw and it's OK for either an empty square or opposite piece is there
    # a value of True means this is for a pawn capture and it's only OK if an opposite piece is there
    # a value of False means this is for a pawn move and it's only OK if an empty square is there
    def generate_moves(self, start, increment, steps, pawn_capture=None):
        start_x, start_y = start
        inc_x, inc_y = increment

        moves = set()
        for i in range(1, steps+1):
            new_x, new_y = start_x+inc_x*i, start_y+inc_y*i
            if not (0 <= new_x < 8 and 0 <= new_y < 8 ):
                break
            
            # check if the square is avaiable to move into
            new_piece = self.get_piece(new_x, new_y)
            if new_piece is None:  # empty square
                if pawn_capture == True: 
                    # if capture is required then it doesn't work unless it's en-passant
                    if self.en_passant_target == new_x and self.back_rank()+5*self.move_direction() == new_y:
                        moves.add( (new_x, new_y) )
                    break 
                moves.add( ( new_x, new_y ) )  # otherwise it's fine and we keep it
            elif new_piece.color == self.active_color: 
                break  # can't take your own piece
            else:
                # opposition piece
                if pawn_capture == False:  
                    break  # this is a pawn move and it cannot take it
                moves.add( ( new_x, new_y ) )  # add the capture as a target
                break   # can't move past opposition piece

        return moves
        
    def get_possible_moves(self, x, y, attacking_only=False):

        # main directions of movement
        cardinal_moves = ( (0,1), (1,0), (0,-1), (-1,0) )
        diagonal_moves = ( (1,1), (1,-1), (-1,-1), (-1,1) )
        knight_moves   = ( (-2, -1), (-1, -2), (-2, 1), (-1, 2), (2, -1), (1, -2), (2, 1), (1, 2) )

        # directions by piece (not including pawns)
        moves_by_piece = { KING   : (cardinal_moves + diagonal_moves, 1),
                           QUEEN  : (cardinal_moves + diagonal_moves, 7),
                           KNIGHT : (knight_moves, 1),
                           BISHOP : (diagonal_moves, 7),
                           ROOK   : (cardinal_moves, 7) }
                           
        piece = self.get_piece(x,y)

        allmoves = set()
        pawn_capture = None
        if piece.name == PAWN:

            direction = self.move_direction()
            pawns_rank = self.back_rank() + direction

            # is this the first move for the pawn
            steps = 2 if y == pawns_rank else 1

            # pawn can only move forward so only one possible path
            increments = () if attacking_only else ( (0, direction), )
            pawn_capture = False
            
            for increment in ( (-1, direction), (1, direction) ):
                moves = self.generate_moves( (x,y), increment, 1, pawn_capture = True )
                if moves:
                    allmoves.update(moves)

        else:
            increments, steps = moves_by_piece[piece.name]
        
        for increment in increments:
            moves = self.generate_moves( (x,y), increment, steps, pawn_capture=pawn_capture )
            if moves:
                allmoves.update(moves)

        if piece.name == KING:
            if self.castles_available[self.active_color][KING]:
                moves = self.generate_moves( (x,y), (1,0), 2 )
                if moves:
                    allmoves.update(moves)
            if self.castles_available[self.active_color][QUEEN]:
                moves = self.generate_moves( (x,y), (-1,0), 2)
                # for queenside castling we also need to make sure the rook can move
                # to assure that all the square between rook and king are empty
                if moves and self.generate_moves( (0, y), (1,0), 1):
                    allmoves.update(moves)
                    
        return allmoves

    # checks a move's validity given the start and end coordinates
    # does not care if the king would end up being under check
    def is_valid_move(self, start, end):
        if start == end:
            return False

        start_piece = self.get_piece(*start)
        end_piece = self.get_piece(*end)

        logging.debug("Start piece is {}".format(start_piece))
        logging.debug("End piece is {}".format(end_piece))

        if start_piece is None:
            return False

        if start_piece.color != self.active_color:
            logging.info("Start piece is not of the active color")
            return False
        
        if end_piece is not None and start_piece.color == end_piece.color:
            logging.info("Start piece and end piece are of the same color")
            return False

        moves = self.get_possible_moves(*start)

        logging.debug("Possible squres to move into: {}".format(', '.join([c2n(*m) for m in moves])))
        if end not in moves:
            return False

        return True

    def is_check(self):
        king = None
        opponent_moves = set()

        # need to get the moves from the opposing player's perspective
        board = copy.deepcopy(self)
        board.flip_active_color()

        for i in range(8):
            for j in range(8):
                piece = self.get_piece(i,j)
                if piece is None:
                    continue
                if piece.color != self.active_color:
                    moves = board.get_possible_moves(i,j, attacking_only=True)
                    if moves:
                        opponent_moves.update(moves)
                elif piece.name == KING and piece.color == self.active_color:
                    king = (i,j)
        
        logging.debug("King: {}".format(c2n(*king)))
        logging.debug("Squares under attack: {}".format(', '.join(sorted([c2n(*m) for m in opponent_moves]))))

        if king in opponent_moves:
            return True

        return False


    def would_be_check(self, start, end):
        board = copy.deepcopy(self)
        
        # need to not enforce_check otherwise we'd end up with infinite recursion
        board.make_move(start, end, enforce_check=False)
        board.flip_active_color()
        return board.is_check()

    # performs all the state updates for the move
    # 1. checks validity & legality/check
    # 2. updates castling state if necessary
    # 3. updates en-passant state if necessary
    # 4. updates 50 move rule counter
    # 5. updates game move counter
    # 6. moves piece (including rook if it's castling)
    # 7. switches the active color to the opposite
    def make_move(self, start, end, enforce_check=True):
        start_x, start_y = start
        end_x, end_y = end

        start_piece = self.get_piece(*start)
        end_piece = self.get_piece(*end)

        if not self.is_valid_move(start, end):
            logging.info("Invalid move")
            return

        if enforce_check:
            # check if this a castling move and confirm that the 
            # king isn't currently in check or would be in check
            if start_piece.name == KING and abs(start_x-end_x) == 2:
                if self.is_check():
                    logging.info("Cannot castle while in check")
                    return
                
                direction = (end_x - start_x)/2
                if self.would_be_check(start, (start_x+direction, start_y)):
                    logging.info("Cannot castle through check")
                    return

            if self.would_be_check(start, end):
                logging.info("Move would result with king being in check")
                return


        ## CASTLING STATE
        if start_piece.name == KING:
            self.castles_available[self.active_color][KING] = False
            self.castles_available[self.active_color][QUEEN] = False

        if start_piece.name == ROOK:
            if start_y == self.back_rank():
                if start_x == 7: # H file
                    self.castles_available[self.active_color][KING] = False
                if start_x == 0: # A file
                    self.castles_available[self.active_color][QUEEN] = False

        ## 50 MOVE RULE COUNTER
        if start_piece.name != PAWN and end_piece is None:
            self.half_move_clock += 1
        else:
            self.half_move_clock = 0
        
        ## MOVE THE PIECE
        self.board[start_x][start_y] = None
        self.board[end_x][end_y] = start_piece

        self.en_passant_target = None
        ## PROMOTION OR EN PASSANT POSSIBILITIES
        if start_piece.name == PAWN:
            # check if this is promotion and make the pawn a Queen
            if 7 - end_y == self.back_rank():
                self.board[end_x][end_y] = Piece(QUEEN, self.active_color)

            ## was this an en-passant capture ?
            if end_piece is None and start_x != end_x:
                # remove the captured pawn
                self.board[end_x][start_y] = None

            ## UPDATE EN PASSANT STATE
            if abs(start_y-end_y) == 2:
                # store only the file because we always know what the rank is based on the color involved
                self.en_passant_target = start_x

        ## MOVE ROOK IN CASE OF CASTLING
        if start_piece.name == KING and abs(start_x-end_x) == 2:
            direction, rook_file = -1, 7 # defaults for kingside castling
            if end_x < start_x: # is it queenside?
                direction, rook_file = 1, 0

            self.board[end_x+direction][start_y] = self.board[rook_file][start_y]
            self.board[rook_file][start_y] = None

        ## MOVE COUNTER
        if self.active_color == BLACK:
            self.full_move_number += 1

        ## FLIP ACTIVE COLOR
        self.flip_active_color()

        ## DONE
        logging.debug("Current board position\n{}\n".format(self))

    def legal_moves_left(self):
        # now test all the moves to see if any of them gets us out of check
        for i in range(8):
            for j in range(8):
                piece = self.get_piece(i,j)
                if piece is None:
                    continue
                if piece.color == self.active_color:
                    moves = self.get_possible_moves(i,j)
                    for move in moves:
                        if not self.would_be_check( (i,j), move ):
                            return True
        return False
        
    # returns None if the game isn't done
    # returns the string reason for the end of game otherwise
    def game_over(self):

        if not self.legal_moves_left():
            reason = "Stalemate"
            if self.is_check():
                reason = "Checkmate"

            return reason
        
        if self.half_move_clock == 100:
            return "Fifty-move Rule"

        # Threefold repetition

        # Insufficient material
        return None
        
def main():
    b = Board()
    error = "Move entry should be of the form a2-a4 where a2 is the start square and a4 is the end square"
    while True:
        logging.info("Current position")
        logging.info(b)
        move = raw_input("Enter move for {}:".format(b.active_color))
        start, end = move.lower().split('-')
        if len(start) != 2 or len(end) != 2:
            logging.warning(error)
            continue
        if start[0] not in 'abcdefgh' or end[0] not in 'abcdefgh':
            logging.warning(error)
            continue
        if start[1] not in '12345678' or end[1] not in '12345678':
            logging.warning(error)
            continue
        
        start = (ord(start[0]) - ord('a'), ord(start[1]) - ord('1'))
        end = (ord(end[0]) - ord('a'), ord(end[1]) - ord('1'))

        b.make_move(start, end)
        
        

if __name__ == "__main__":
    main()




