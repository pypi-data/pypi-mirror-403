from chess_2d.Game_Engine.Game_utils import board_printing,user_input_handling,perform_move,common_functions
from chess_2d.Game_Engine.Game_Rules.possible_position import Possible_Position

def print_board(board:complex):
    board_printing.print_board(board)
    print(f"{board.current_player}'s move")

def take_user_input(board:complex):
   return user_input_handling.take_user_input(board)
    

def update_piece_position(board:compile,source_cell:str,distination_cell:str):
    perform_move.update_piece_on_board(board,source_cell,distination_cell)
    Possible_Position(board) # updating possible positions after every move
    update_current_player(board)


def get_winner(board:complex):
    return board.current_player

def update_current_player(board:complex):
    board.current_player=common_functions.change_current_player(board)

def is_restart_board(board:complex)-> bool:
    if board_printing.show_restart_option(board):
            board=common_functions.reset_board_pieces(board)
            board_printing.redraw_board(board)
            return True
    else:
        board.running=False
        board.main_window.destroy()
        return False

