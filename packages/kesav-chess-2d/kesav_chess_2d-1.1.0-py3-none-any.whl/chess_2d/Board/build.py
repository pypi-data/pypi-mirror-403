import copy

from chess_2d.Game_Engine import static_variables
from chess_2d.Game_Engine.Error_handler import set_error
from chess_2d.Game_Engine.Game_utils import common_functions


class Board:
    white=copy.deepcopy(static_variables.white)
    black=copy.deepcopy(static_variables.black)
    white_possible_positions={}
    black_possible_positions={}
    piece_ref=static_variables.piece_ref
    col_ref=static_variables.col_ref
    row_ref=static_variables.row_ref
    current_player='white'
    error=set_error.Error()
    running=True
    main_window=None
    canvas =None

    selected_cell=None
        

def build_board(self):
    return Board()