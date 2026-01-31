from chess_2d.Game_Engine import static_variables
from chess_2d.Game_Engine.Game_utils import common_functions
from chess_2d.Game_Engine.Error_handler import set_error
import copy
class Board:
    yellow=copy.deepcopy(static_variables.yellow)
    green=copy.deepcopy(static_variables.green)
    yellow_possible_positions={}
    green_possible_positions={}
    piece_ref=static_variables.piece_ref
    col_ref=static_variables.col_ref
    row_ref=static_variables.row_ref
    current_player='yellow'
    error=set_error.Error()
    running=True
    main_window=None
    canvas =None

    selected_cell=None
        

def build_board(self):
    return Board()