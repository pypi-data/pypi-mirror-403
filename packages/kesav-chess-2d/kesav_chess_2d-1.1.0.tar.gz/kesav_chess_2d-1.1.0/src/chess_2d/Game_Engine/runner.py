from chess_2d.Game_Engine.Error_handler import set_error,error_printer
from chess_2d.Game_Engine.Game_Rules import move_validator,game_rules
from chess_2d.Game_Engine.Game_utils import util,common_functions,board_printing

def runner(board):
    
    board_printing.print_board(board)
    perform_move(board)
    board.main_window.mainloop()


def perform_move(board):

    if game_rules.is_check(board):
            board_printing.print_message(board,text=f"Check for {board.current_player} player")

    if game_rules.is_check_mate(board):

        board_printing.print_message(board,text=f" {util.get_winner(board)} player WON")
        if not util.is_restart_board(board):
            exit(0) 
        
    
    input=util.take_user_input(board)
    if input is None:
        print("Game exited")
        exit(0)

    source_cell,destination_cell=map(str,input)
    
    if move_validator.is_legal_move(board,source_cell,destination_cell):
        util.update_piece_position(board,source_cell,destination_cell)
        board_printing.redraw_board(board)
    else:
        error_printer.Print_message(board, set_error.Error(False, 'illegal_move', f"illegal move"))
    board.main_window.after(0, lambda: perform_move(board))
        
    
    
    