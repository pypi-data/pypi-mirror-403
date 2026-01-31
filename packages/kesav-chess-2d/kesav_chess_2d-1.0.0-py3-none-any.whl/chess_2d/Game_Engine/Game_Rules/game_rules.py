# check, checkmate, castling, en passant, promotion

def is_check(board):
    # variables
    current_player_name = board.current_player
    oppenent_player_name = 'green' if current_player_name == 'yellow' else 'yellow'
    current_player_data= getattr(board,current_player_name)

    opponent_player_possible_positions= getattr(board,oppenent_player_name+'_possible_positions')
    current_player_king_pos=current_player_data['king'][0]

    if is_in_check(current_player_king_pos,opponent_player_possible_positions):
        return True
    return False

def is_in_check(king_pos,possible_positions):
    for piece_type in possible_positions:
        for pos in possible_positions[piece_type]:
            if king_pos in pos['captures']:
                return True
    return False

def is_check_mate(board):
    oppenent_player_name = 'green' if board.current_player == 'yellow' else 'yellow'
    oppenent_player_data= getattr(board,oppenent_player_name)
    
    opponent_player_king_pos=oppenent_player_data['king'][0]
    current_player_possible_positions= getattr(board,board.current_player+'_possible_positions')

    if is_in_check(opponent_player_king_pos,current_player_possible_positions):
        return True
    return False
