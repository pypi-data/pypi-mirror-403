from chess_2d.Game_Engine.Game_utils import common_functions

def update_piece_on_board(board:compile,source_cell:str,distination_cell:str):
    # variables
    player_name=board.current_player
    player_data=getattr(board,player_name)
    
    piece_type=common_functions._piece_type_at_cell(source_cell,player_data)
    positon=common_functions._piece_index_at_cel(source_cell,player_data)

    if common_functions.is_cell_occupied(distination_cell,board):
        common_functions.remove_piece_at_cell(distination_cell,board) # capturing the piece

    player_data[piece_type][int(positon)]=distination_cell
