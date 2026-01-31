from chess_2d.Game_Engine.Error_handler import set_error
from chess_2d.Game_Engine.Game_utils import common_functions
from chess_2d.Game_Engine import static_variables
import tkinter as tk

def take_user_input(board:complex):
    user_input=take_input_from_gui(board)
    return user_input

def on_close(board, done_var):
    board.running = False
    done_var.set(True)     
    board.main_window.destroy()


def take_input_from_gui(board:complex) -> str:
    source_cell,distination_cell=None,None
    done = tk.BooleanVar(value=False)
    board.main_window.protocol(
        "WM_DELETE_WINDOW",
        lambda: on_close(board, done)
    )

    def get_cell(event):
        col=event.x // static_variables.cell_size 
        row=event.y // static_variables.cell_size +1
        if not (0 < row <= 8 and 0 <= col <= 8):
            return
        cell=common_functions.index_to_cell(row,col)
        
        if board.selected_cell is None:
            nonlocal source_cell
            source_cell=cell
            board.selected_cell=cell
        else:
            nonlocal distination_cell
            distination_cell=cell
            board.selected_cell=None
            done.set(True)

        
    board.main_window.bind("<Button-1>", lambda event: get_cell(event))
    board.main_window.wait_variable(done)

    if not board.running:
        return None   # signal exit
    
    board.main_window.unbind("<Button-1>")

    

    return [source_cell, distination_cell]
    
