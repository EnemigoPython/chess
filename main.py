import pygame as pg
from pygame import freetype
import pieces
import sys

w = 660
h = 490
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (142, 142, 142)
SILVER = (192, 192, 192)
LIGHT = (252, 204, 116)
DARK = (87, 58, 46)
GREEN = (0, 255, 0)
RED = (215, 0, 0)
ORANGE = (255, 165, 0)
transcript, turn_number = '', 0


def coords_to_notation(coords):
    return f'{chr(97 + coords[0])}{8 - coords[1]}'


def notation_to_coords(notation):
    return ord(notation[0]) - 97, 8 - int(notation[1])


def reset_board(with_pieces=True):
    def generate_pieces(colour):
        return [pieces.Rook(colour), pieces.Knight(colour), pieces.Bishop(colour), pieces.Queen(colour),
                pieces.King(colour), pieces.Bishop(colour), pieces.Knight(colour), pieces.Rook(colour)]

    board = [[None for x in range(8)] for x in range(8)]
    if with_pieces:
        board[0] = generate_pieces("black")
        board[7] = generate_pieces("white")
        board[1] = [pieces.Pawn("black") for square in board[1]]
        board[6] = [pieces.Pawn("white") for square in board[6]]
    return board


def draw_squares(screen):
    colour_dict = {True: LIGHT, False: DARK}
    current_colour = True
    for row in range(8):
        for square in range(8):
            pg.draw.rect(screen, colour_dict[current_colour], ((40 + (square * 50)), 40 + (row * 50), 50, 50))
            current_colour = not current_colour
        current_colour = not current_colour


def draw_coords(screen, font, flipped):
    for row in range(8):
        if flipped:
            font.render_to(screen, (10, 45 + (row * 50)), chr(49 + row))
        else:
            font.render_to(screen, (10, 45 + (row * 50)), chr(56 - row))
    for col in range(8):
        if flipped:
            font.render_to(screen, (45 + (col * 50), 450), chr(72 - col))
        else:
            font.render_to(screen, (45 + (col * 50), 450), chr(65 + col))


def draw_pieces(screen, font, board, flipped):
    for row, pieces in enumerate(board[::(-1 if flipped else 1)]):
        for square, piece in enumerate(pieces[::(-1 if flipped else 1)]):
            if piece:
                font.render_to(screen, (piece.img_adjust[0] + (square * 50), piece.img_adjust[1] + (row * 50)),
                               piece.image, BLACK)


def find_square(x, y, flipped):
    true_target = int((x - 40) / 50), int((y - 40) / 50)
    if flipped:
        target_square = 7 - true_target[0], 7 - true_target[1]
    else:
        target_square = true_target
    return true_target, target_square


def draw_text(screen, font, turn, colour, check, playing, promotion, auto_flip):
    counter_colour = BLACK if turn == 'white' else WHITE
    pg.draw.rect(screen, BLACK, (450, 45, 205, 130), width=1)
    pg.draw.rect(screen, BLACK, (450, 345, 205, 130), width=1)
    pg.draw.rect(screen, colour, (450, 190, 200, 140))
    if playing:
        font.render_to(screen, (465, 200), f'{turn} to move', counter_colour)
    else:
        font.render_to(screen, (465, 200), f'{turn} wins', counter_colour)
    pg.draw.rect(screen, counter_colour, (465, 230, 20, 20), width=3)
    if auto_flip:
        font.render_to(screen, (465, 230), '✓', GREEN)
    font.render_to(screen, (490, 230), 'auto-rotate', counter_colour)
    promote_dict = {'queen': 9813, 'rook': 9814, 'bishop': 9815, 'knight': 9816}
    font.render_to(screen, (465, 260), f'promote: {chr(promote_dict[promotion])}', counter_colour)
    if check:
        font.render_to(screen, (465, 300), ('CHECK' if playing else 'CHECKMATE'), counter_colour if playing else RED)


def draw_legal_moves(screen, colour, moves, board, flipped):
    for move in moves:
        if flipped:
            pg.draw.circle(screen, colour, ((65 + ((7 - move[0]) * 50), 65 + ((7 - move[1]) * 50))), 5)
        else:
            pg.draw.circle(screen, colour, ((65 + (move[0] * 50), 65 + (move[1] * 50))), 5)


def draw_captures(screen, font, captures, flipped):
    for e, piece in enumerate([i for i in captures if i.colour == ('white' if flipped else 'black')]):
        if e < 6:
            font.render_to(screen, (400 + piece.img_adjust[0] + (e * 35), 300 + piece.img_adjust[1]), piece.image,
                           BLACK)
        elif e < 12:
            font.render_to(screen, (400 + piece.img_adjust[0] + ((e - 6) * 35), 340 + piece.img_adjust[1]), piece.image,
                           BLACK)
        else:
            font.render_to(screen, (400 + piece.img_adjust[0] + ((e - 12) * 35), 380 + piece.img_adjust[1]),
                           piece.image, BLACK)
    for e, piece in enumerate([i for i in captures if i.colour == ('black' if flipped else 'white')]):
        if e < 6:
            font.render_to(screen, (400 + piece.img_adjust[0] + (e * 30), piece.img_adjust[1]), piece.image, BLACK)
        elif e < 12:
            font.render_to(screen, (400 + piece.img_adjust[0] + ((e - 6) * 35), 40 + piece.img_adjust[1]), piece.image,
                           BLACK)
        else:
            font.render_to(screen, (400 + piece.img_adjust[0] + ((e - 12) * 35), 80 + piece.img_adjust[1]), piece.image,
                           BLACK)


def move_piece(board, target, kings, origin, destination, captures, promotion):
    global transcript, turn_number
    # start transcript
    if target.colour == 'white':
        turn_number += 1
        transcript += f'{turn_number}. '

    # piece move conditions
    for row in board:
        for piece in row:
            if piece and piece.name == 'pawn' and piece.en_passant:
                piece.en_passant = False
    promoting = False
    if target.name == 'pawn':
        if target.double_move:
            target.double_move = False
        if abs(origin[1] - destination[1]) == 2:
            target.en_passant = True
        if origin[0] != destination[0] and not board[destination[1]][destination[0]]:
            captures.append(board[destination[1] - target.direction][destination[0]])
            board[destination[1] - target.direction][destination[0]] = None
            transcript += coords_to_notation(origin)[0]
        if destination[1] == (0 if target.colour == 'white' else 7):
            promoting = True
            piece_dict = {'queen': pieces.Queen(target.colour), 'knight': pieces.Knight(target.colour),
                          'rook': pieces.Rook(target.colour), 'bishop': pieces.Bishop(target.colour)}
    if target.name == 'king':
        kings[int(target.colour == "black")] = destination
        if target.castle_rights:
            target.castle_rights = False
        if destination[0] - origin[0] == 2:
            board[target.back_rank][5] = board[target.back_rank][7]
            board[target.back_rank][7] = None
            transcript += 'O-O '
        if origin[0] - destination[0] == 2:
            board[target.back_rank][3] = board[target.back_rank][0]
            board[target.back_rank][0] = None
            transcript += 'O-O-O '
    if target.name == 'rook' and target.castle_rights:
        target.castle_rights = False

    # finish transcript
    if transcript[-2] != 'O':
        if target.name != 'pawn':
            transcript += target.name[0].upper() if target.name != 'knight' else 'N'
        elif board[destination[1]][destination[0]]:
            transcript += coords_to_notation(origin)[0]
        transcript += f'x{coords_to_notation(destination)} ' if board[destination[1]][destination[0]] else f'{coords_to_notation(destination)} '

    # add any existing piece to captures list
    if board[destination[1]][destination[0]]:
        captures.append(board[destination[1]][destination[0]])

    # move piece
    if not promoting:
        board[destination[1]][destination[0]] = target
    else:
        board[destination[1]][destination[0]] = piece_dict[promotion]
        transcript += f'={promotion[0].upper()} ' if promotion != 'knight' else '=N'
    board[origin[1]][origin[0]] = None

    # any checks with new board status
    enemy_king = kings[int(target.colour == "white")]
    check = board[enemy_king[1]][enemy_king[0]].in_check(board, enemy_king)
    return board, captures, kings, check


def draw_check(screen, board, kings, flipped, turn, checkmate):
    if checkmate:
        king = kings[1 if turn == 'white' else 0]
    else:
        king = kings[0 if turn == 'white' else 1]
    if flipped:
        pg.draw.circle(screen, RED if checkmate else ORANGE, ((65 + ((7 - king[0]) * 50), 65 + ((7 - king[1]) * 50))),
                       25, width=3)
    else:
        pg.draw.circle(screen, RED if checkmate else ORANGE, ((65 + (king[0] * 50), 65 + (king[1] * 50))), 25, width=3)


def checkmate(board, turn, kings):
    global transcript
    for y, row in enumerate(board):
        for x, square in enumerate(row):
            if square and square.colour != turn:
                moves = square.find_moves(board, (x, y), kings, True)
                if moves:
                    transcript = transcript[:-1] + '+ '
                    return False
    transcript = transcript[:-1] + '# '
    return True


def main():
    global transcript, turn_number
    # window init
    pg.init()
    clock = pg.time.Clock()
    window_logo = pg.image.load('chess_piece_king.png')
    pg.display.set_caption('Chess')
    pg.display.set_icon(window_logo)
    screen = pg.display.set_mode((w, h))

    # font/pieces init: the piece icons come from the unicode of this font
    freetype.init()
    font = freetype.Font('FreeSerif-4aeK.ttf', 50)
    micro_font = freetype.Font('FreeSerif-4aeK.ttf', 25)

    # board init
    board = reset_board()

    # declare vars
    playing = True
    turn = 'white'
    check = False
    board_flipped = False
    auto_flip = False
    kings = [(4, 7), (4, 0)]
    promotion = 'queen'
    target_square = None
    target = None
    captures = []
    legal_moves = []

    while True:
        screen.fill(GREY)
        COLOUR = SILVER if turn == 'white' else BLACK
        draw_squares(screen)
        if target_square:
            pg.draw.rect(screen, COLOUR, ((40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50), width=2)
        draw_coords(screen, font, board_flipped)
        draw_pieces(screen, font, board, board_flipped)
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                if playing and 441 > event.pos[0] > 39 and 441 > event.pos[1] > 39:
                    if event.button != 3:
                        true_target, target_square = find_square(event.pos[0], event.pos[1], board_flipped)
                        target = board[target_square[1]][target_square[0]]
                        if target and turn == target.colour:
                            legal_moves = target.find_moves(board, target_square, kings, check)
                    elif target_square and target:
                        true_target, destination = find_square(event.pos[0], event.pos[1], board_flipped)
                        if destination in legal_moves:
                            board, captures, kings, check = move_piece(board, target, kings, target_square, destination,
                                                                       captures, promotion)
                            if check and checkmate(board, turn, kings):
                                playing = False
                                target_square = None
                            else:
                                turn = 'black' if turn == 'white' else 'white'
                                if auto_flip and board_flipped == (turn == 'white'):
                                    board_flipped = not board_flipped
                                    if target_square:
                                        true_target = 7 - true_target[0], 7 - true_target[1]
                            legal_moves = []
                        else:
                            target_square = None
                    else:
                        target_square = None
                else:
                    target_square = None
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    board_flipped = not board_flipped
                    if target_square:
                        true_target = 7 - true_target[0], 7 - true_target[1]
                if event.key == pg.K_r:
                    board = reset_board()
                    kings = [(4, 7), (4, 0)]
                    turn = 'white'
                    check = False
                    board_flipped = False
                    target_square = None
                    captures = []
                    playing = True
                    transcript, turn_number = '', 0
                if event.key == pg.K_a:
                    auto_flip = not auto_flip
                if event.key == pg.K_1:
                    promotion = 'queen'
                if event.key == pg.K_2:
                    promotion = 'knight'
                if event.key == pg.K_3:
                    promotion = 'rook'
                if event.key == pg.K_4:
                    promotion = 'bishop'
                if event.key == pg.K_p:
                    print(transcript)
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
        draw_text(screen, micro_font, turn, COLOUR, check, playing, promotion, auto_flip)
        if target_square and target and turn == target.colour and legal_moves:
            draw_legal_moves(screen, COLOUR, legal_moves, board, board_flipped)
        if captures:
            draw_captures(screen, font, captures, board_flipped)
        if check:
            draw_check(screen, board, kings, board_flipped, turn, not playing)
        pg.display.update()
        clock.tick(60)


if __name__ == '__main__':
    main()
