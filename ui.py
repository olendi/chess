import Tkinter as tk
import board
import logging
import os

logging.basicConfig(level=logging.DEBUG)

DARK_SQUARE_COLOR = '#58ae8b'
LIGHT_SQUARE_COLOR = '#feffed'

SQUARE_SIZE = 64

MYDIR = os.path.dirname(os.path.realpath(__file__))

class Chess(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.grid()
        self.chess_board = board.Board()

        self.canvas = tk.Canvas(self, width=8*SQUARE_SIZE, height=8*SQUARE_SIZE)

        # used to track information when moving pieces
        self._drag_data = {"x": 0, "y": 0, "item": None, "start" : None}

        # in addition to easy lookup, ref's to PhotoImage must be kept, else the
        # surrounding image (from canvas.create_image()) will be left empty
        self.piece2photo = {}
        for piece in 'pnbrqk':
            self.piece2photo[piece] = tk.PhotoImage(file=MYDIR+'/images/black/%s.gif' % piece)
        for piece in 'PNBRQK':
            self.piece2photo[piece] = tk.PhotoImage(file=MYDIR+'/images/white/%s.gif' % piece)

        for ridx, rname in enumerate(list('87654321')):
            for fidx, fname in enumerate(list('abcdefgh')):
                tag = fname + rname
                color = [LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR][(ridx-fidx)%2]
                shade = ['light', 'dark'][(ridx-fidx)%2]

                tags = [fname+rname, shade, 'square']

                self.canvas.create_rectangle(
                    fidx*SQUARE_SIZE, ridx*SQUARE_SIZE,
                    fidx*SQUARE_SIZE+SQUARE_SIZE, ridx*SQUARE_SIZE+SQUARE_SIZE,
                    outline=color, fill=color, tag=tags)
        
        self.canvas.grid(row=0, column=0)
        self.refresh_canvas()

        self.quitButton = tk.Button(self, text='Quit', command=self.quit)
        self.quitButton.grid(columnspan=2)

        self.newButton = tk.Button(self, text='New Game', command=self.reset_board)
        self.newButton.grid(columnspan=2)

    def reset_board(self):
        self.chess_board = board.Board()
        self.refresh_canvas()

    def place_piece(self, square, piece):
        # canvas rectangle objects are tagged with 'a1', etc.
        item = self.canvas.find_withtag(square)
        # get bounding box of rectangle (we'll draw piece here)
        coords = self.canvas.coords(item)
        # do it
        photo = self.piece2photo[str(piece)]
        image = self.canvas.create_image(coords[0], coords[1], image=photo,
                                         state=tk.NORMAL, anchor=tk.NW, tag='piece')

    def refresh_canvas(self):
        self.canvas.delete('piece')

        for x, fname in enumerate(list('abcdefgh')):
            for y, rname in enumerate(list('12345678')):
                sname = fname + rname

                piece = self.chess_board.get_piece(x,y)
                if piece is not None:
                    self.canvas.update_idletasks()
                    self.place_piece(sname, piece)

        # add bindings for clicking, dragging and releasing over
        # any object with the "piece" tag
        self.canvas.tag_bind("piece", "<ButtonPress-1>", self.piece_press)
        self.canvas.tag_bind("piece", "<ButtonRelease-1>", self.piece_release)
        self.canvas.tag_bind("piece", "<B1-Motion>", self.piece_motion)

    def piece_press(self, event):
        '''Begining drag of an object'''
        # record the item and its location
        self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]

        self._drag_data["start"] =  (event.x / SQUARE_SIZE, 7 - event.y / SQUARE_SIZE)
        logging.debug("Starting coords {}".format(board.c2n(*self._drag_data["start"])))

        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def piece_release(self, event):
        '''End drag of an object'''
        # figure out where we are right now
        end = (event.x / SQUARE_SIZE, 7 - event.y / SQUARE_SIZE)
        logging.debug("Ending coords {}".format(board.c2n(*end)))

        self.chess_board.make_move(self._drag_data["start"], end)
        self.refresh_canvas()

        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["start"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def piece_motion(self, event):
        '''Handle dragging of an object'''
        # compute how much the mouse has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]

        # raise the object to the top of the display list
        self.canvas.tag_raise(self._drag_data["item"])

        # move the object the appropriate amount
        self.canvas.move(self._drag_data["item"], delta_x, delta_y)

        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
