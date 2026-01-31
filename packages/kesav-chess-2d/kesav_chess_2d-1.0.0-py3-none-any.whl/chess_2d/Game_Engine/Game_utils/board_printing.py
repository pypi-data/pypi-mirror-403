import tkinter as tk
from chess_2d.Game_Engine.Game_utils import common_functions
from chess_2d.Game_Engine import static_variables
from importlib.resources import files


width,height=static_variables.cell_size * 8 ,static_variables.cell_size * 8  

def print_board(board:complex):
    
    if board.main_window is None:
        board.main_window=tk.Tk()
        board.main_window.title("Chess 2D - Sai Kesav")
        board.canvas=tk.Canvas(board.main_window, width=width, height=height)
        board.canvas.pack()
        
    redraw_board(board)
    return board.canvas
    
def show_restart_option(board:complex)-> bool:
    from tkinter import messagebox
    result = messagebox.askyesno("Game Over", "Do you want to restart the game?")
    return result
    

def redraw_board(board:complex):
    canvas=board.canvas
    canvas.delete("all")
    braw_base(canvas)
    update_current_player_title(board)
    put_pieces_on_board(canvas, board.yellow, board.green)

def braw_base(canvas):
    
    colors = ("#f0d9b5", "#b58863")

    for r in range(8):
        for c in range(8):
            canvas.create_rectangle(
                c*static_variables.cell_size,
                r*static_variables.cell_size,
                (c+1)*static_variables.cell_size,
                (r+1)*static_variables.cell_size,
                fill=colors[(r+c) % 2],
                outline=""
            )

def put_pieces_on_board(canvas,yellow,green):
    
    canvas.images=[]    

    for player_name,player_data in (['green',green],['yellow',yellow]):
        put_one_player_pieces(canvas,player_name,player_data)
    return 
    

def put_one_player_pieces(canvas,player_name,player_data):
    file_name= "white_" if player_name == 'yellow' else "black_"
    folder_path="img\\"+file_name

    for type,pieces in player_data.items():
        for pos in pieces:
            file_path=folder_path+(type+'.png')
            file_path=files("chess_2d").joinpath(file_path)
            row,col=common_functions.cell_to_index(pos)

            img=tk.PhotoImage(file=file_path)
            canvas.images.append(img)  
            canvas.create_image(col*static_variables.cell_size, row*static_variables.cell_size, image=img, anchor="nw")

    return


def print_message(board,text:str):
    canvas=board.canvas

    canvas.update_idletasks()
    w = canvas.winfo_width()
    h = canvas.winfo_height()

    canvas.delete("message") 
    canvas.create_text(
        w//2,
        h//2,
        text=text,
        fill="black",
        font=("Helvetica", 16, "bold"),
        tags="message",
        anchor="center"
    )

    # Remove the check message after 3 seconds
    canvas.after(2000, lambda: canvas.delete("message"))
    return

def update_current_player_title(board:complex):
    board.main_window.title(f"Chess 2D - Sai Kesav | Current Player: {board.current_player.capitalize()}")
    return
