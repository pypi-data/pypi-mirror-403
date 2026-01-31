# legal moves, captures, checks, pins
from chess_2d.Game_Engine import static_variables
from chess_2d.Game_Engine.Game_Rules.possible_position import Possible_Position
from chess_2d.Game_Engine.Game_utils import common_functions

def is_legal_move(board,source_cell,distination_cell):
    player=board.current_player
    player_data=getattr(board,player)

    if not getattr(board,board.current_player+"_possible_positions"): # sets possible positions if not set
        Possible_Position(board)

    piece_type=common_functions._piece_type_at_cell(source_cell,player_data)
    piece_index=common_functions._piece_index_at_cel(source_cell,player_data)

    if _in_bounds(source_cell) and _in_bounds(distination_cell):
        if is_cell_belongs_to_current_player(player_data,source_cell):
            current_piece_Possible_positions=getattr(board,board.current_player+"_possible_positions")[piece_type][piece_index]['moves'] + getattr(board,board.current_player+"_possible_positions")[piece_type][piece_index]['captures']
            if distination_cell in current_piece_Possible_positions: # legal move
                return True
            
    return False
    
def is_cell_belongs_to_current_player(player_data,cell):
    for key,values in  player_data.items():
        if cell in values:
            return True
    return False


def _in_bounds(cell:str):
    alphs_part=cell[0]
    nums_part=cell[1]

    if alphs_part in static_variables.col_ref and nums_part in static_variables.row_ref:
        return True
    return False