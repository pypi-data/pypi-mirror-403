from chess_2d.Game_Engine.static_variables import col_ref,row_ref
from chess_2d.Game_Engine import static_variables
import copy

def cell_to_index(text:str):
    text=list(text)
    col=text[0]
    row=text[1]
    return int(row_ref.index(row)),int(col_ref.index(col))

def index_to_cell(row:int,col:int):
    return col_ref[col]+str(row)

def clrscr(board:complex):
    board.main_window.destroy()
    return

def reset_board_pieces(board:complex):
    board.yellow={}
    board.green={}
    board.yellow=copy.deepcopy(static_variables.yellow)
    board.green=copy.deepcopy(static_variables.green)
    board.yellow_possible_positions={}
    board.green_possible_positions={}
    board.current_player='yellow'
    board.selected_cell=None
    return board

def _piece_type_at_cell(cell:str,player:complex)-> str:
    type:str=None
    for piece_type,pieces in player.items():
        for piece in pieces:
            if piece==cell:
                type=piece_type
                break
    return type if type else ''

def _piece_index_at_cel(cell:str,player:complex)-> int:
    index:int=-1
    for piece_type,pieces in player.items():
        for piece in pieces:
            if piece==cell:
                index=pieces.index(cell)
                break
    return index if index != -1 else -1

def is_cell_occupied(cell:str,board:complex)->bool:
    for player_name in ['yellow','green']:
        player_data=getattr(board,player_name)
        for _,pieces in player_data.items():
            if cell in pieces:
                return True
    return False

def remove_piece_at_cell(cell:str,board:complex):
    for player_name in ['yellow','green']:
        player_data=getattr(board,player_name)
        for type,pieces in player_data.items():
            if cell in pieces:
                remove_possible_position_data(type,pieces.index(cell),getattr(board,player_name+'_possible_positions')) 
                pieces.remove(cell)  # removing the piece             
                return
            
def remove_possible_position_data(type:str,index:int,possible_position_date:dict):
    possible_position_date[type].pop(index)


def change_current_player(board:complex):
    if board.current_player == 'yellow':
        return 'green'
    else:
        return 'yellow'