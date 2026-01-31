from chess_2d.Board.build import build_board
from chess_2d.Game_Engine.runner import runner


class chess:
    def __init__(self):
        board=build_board(self)
        print("----------------WELCOME TO CHESS --------------")
        print("Close the window anytime to exit the game :)")
        print("-----------------------------------------------")
        print("Made by - Sai Kesav")
        runner(board)
        

chess()