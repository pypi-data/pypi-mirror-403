from chess_2d.Game_Engine.Game_utils import board_printing
def Print_message(board,error:complex):
    # printing the error message on the board canvas
    board_printing.print_message(board,error.message)