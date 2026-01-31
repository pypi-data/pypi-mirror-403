from chess_2d.Game_Engine import static_variables
from chess_2d.Game_Engine.Game_utils import common_functions


class Possible_Position:

    current_player_name:str
    opponent_player_name:str

    current_player_data:complex
    opponent_player_data:complex


    def __init__(self,board:complex):

        self.current_player_name=board.current_player
        self.opponent_player_name='green' if board.current_player == 'yellow' else 'yellow'
        self.current_player_data=getattr(board,self.current_player_name)
        self.opponent_player_data=getattr(board,self.opponent_player_name)


        setattr(board,self.current_player_name+"_possible_positions",self.possible_position())

        self.current_player_name,self.opponent_player_name=self.opponent_player_name,self.current_player_name
        self.current_player_data,self.opponent_player_data=self.opponent_player_data,self.current_player_data
        setattr(board,self.current_player_name+"_possible_positions",self.possible_position())
    

    def possible_position(self) -> dict[str,list[list,list]]: 
        possible_positions={'pawn':[],
                'rook':[],
                'bishop':[],
                'knight':[],
                'king':[],
                'queen':[]
                }
        for piece_type,pieces in self.current_player_data.items():
            for piece in pieces:
                possible_positions[piece_type].append(self.find_possible_positions(piece_type,piece))
        return possible_positions

    def find_possible_positions(self,piece_type:str,cell:str) -> list[list,list]:
        switcher={
            'pawn': self.pawn_possible_positions(cell),
            'rook':  self.rook_possible_positions(cell),
            'bishop':  self.bishop_possible_positions(cell),
            'knight':  self.knight_possible_positions(cell),
            'king':  self.king_possible_positions(cell),
            'queen':  self.queen_possible_positions(cell)
        }
        return switcher.get(piece_type,[])

    def _cells_of(self, player:complex) -> set[str]: # return all occupied cells by a player
        cells = set()
        if isinstance(player, dict):
            for _, pieces in player.items():
                for cell in pieces:
                    if isinstance(cell, str) and len(cell) == 2 and cell != '0':
                        cells.add(cell)
        return cells

    def _to_index(self, cell: str) -> tuple[int, int]:
        col = static_variables.col_ref.index(cell[0])
        row = static_variables.row_ref.index(cell[1])
        return row, col

    def _to_cell(self, row: int, col: int) -> str:
        return static_variables.col_ref[col] + static_variables.row_ref[row]

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def pawn_possible_positions(self, cell: str) -> list:
        moves, captures = [], []
        own = self._cells_of(self.current_player_data)
        opp = self._cells_of(self.opponent_player_data)

        row, col = self._to_index(cell)
        direction = 1 if self.current_player_name == 'yellow' else -1
        start_row = 1 if self.current_player_name == 'yellow' else 6

        # one step forward
        one_r = row + direction
        if self._in_bounds(one_r, col):
            one_cell = self._to_cell(one_r, col)
            if one_cell not in own and one_cell not in opp:
                moves.append(one_cell)

                # two steps from start rank
                two_r = row + (2 * direction)
                if row == start_row and self._in_bounds(two_r, col):
                    two_cell = self._to_cell(two_r, col)
                    if two_cell not in own and two_cell not in opp:
                        moves.append(two_cell)

        # diagonal captures / guards
        for dc in (-1, 1):
            r = row + direction
            c = col + dc
            if self._in_bounds(r, c):
                diag = self._to_cell(r, c)
                if diag in opp:
                    captures.append(diag)
                

        return {'moves': moves, 'captures': captures}

    def rook_possible_positions(self, cell: str) -> list:
        moves, captures = [], []
        own = self._cells_of(self.current_player_data)
        opp = self._cells_of(self.opponent_player_data)

        row, col = self._to_index(cell)
        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)): # delta for row/col and directions right, left, up, down
            r, c = row + dr, col + dc
            while self._in_bounds(r, c):
                nxt = self._to_cell(r, c)
                if nxt in own:
                    break
                if nxt in opp:
                    captures.append(nxt)
                    break
                moves.append(nxt)
                r += dr
                c += dc

        return {'moves': moves, 'captures': captures}

    def bishop_possible_positions(self, cell: str) -> list:
        moves, captures = [], []
        own = self._cells_of(self.current_player_data)
        opp = self._cells_of(self.opponent_player_data)

        row, col = self._to_index(cell)
        for dr, dc in ((1,1), (1,-1), (-1,1), (-1,-1)):
            r, c = row + dr, col + dc
            while self._in_bounds(r, c):
                nxt = self._to_cell(r, c)
                if nxt in own:
                    break
                if nxt in opp:
                    captures.append(nxt)
                    break
                moves.append(nxt)
                r += dr
                c += dc

        return {'moves': moves, 'captures': captures}

    def knight_possible_positions(self, cell: str) -> list:
        moves, captures = [], []
        own = self._cells_of(self.current_player_data)
        opp = self._cells_of(self.opponent_player_data)

        row, col = self._to_index(cell)
        for dr, dc in ((2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)):
            r, c = row + dr, col + dc
            if not self._in_bounds(r, c):
                continue
            nxt = self._to_cell(r, c)
            if nxt in own:
                pass
            elif nxt in opp:
                captures.append(nxt)
            else:
                moves.append(nxt)

        return {'moves': moves, 'captures': captures}

    def king_possible_positions(self, cell: str) -> list:
        moves, captures = [], []
        own = self._cells_of(self.current_player_data)
        opp = self._cells_of(self.opponent_player_data)

        row, col = self._to_index(cell)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if not self._in_bounds(r, c):
                    continue
                nxt = self._to_cell(r, c)
                if nxt in own:
                    pass
                elif nxt in opp:
                    captures.append(nxt)
                else:
                    moves.append(nxt)

        return {'moves': moves, 'captures': captures}

    def queen_possible_positions(self, cell: str) -> list:
        # Combine rook + bishop logic
        r_moves = self.rook_possible_positions(cell)
        b_moves = self.bishop_possible_positions(cell)
        return {'moves': r_moves['moves'] + b_moves['moves'], 'captures': r_moves['captures'] + b_moves['captures']}





