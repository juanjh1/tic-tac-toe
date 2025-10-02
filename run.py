import pygame
from utils import center_rects, draw_lines, Status
from Pices import Pice, XPice, OPice
from Table import Table
from assets_loader import (START_IMG, 
                           WINNER_IMG, 
                           XPICE_IMG,
                            OPICE_IMG,
                            TIE_IMG, RESTART_IMG)
# pygame setup
pygame.init()

turn_dict = {
    "x" : (XPice, "o"),
    "o": (OPice, "x"),

}


WIDTH = 980
HEIGTH = 620
MAIN_RECT_WIDTH = 500
MAIN_RECT_HEIGTH = 500
PIXEL_X = MAIN_RECT_WIDTH // Table.SIZE
PIXEL_Y = MAIN_RECT_HEIGTH  // Table.SIZE

screen = pygame.display.set_mode((WIDTH, HEIGTH))
clock = pygame.time.Clock()

running = True


main_rect = pygame.Rect(center_rects(WIDTH, MAIN_RECT_WIDTH) , center_rects(HEIGTH, MAIN_RECT_HEIGTH),MAIN_RECT_WIDTH,MAIN_RECT_HEIGTH)
table = None

turn = "x"
winer_img = None
current_status = Status.MENU
next_turn = 1
pice_in_game = 0
tie_conunter = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()  
            cartesian_x = 0
            cartesian_y = 1
            if(current_status == Status.INGAME):
             
                if  (pos[cartesian_x] > main_rect.left and pos[cartesian_x] < MAIN_RECT_WIDTH + main_rect.left):
                    x = (pos[cartesian_x] - main_rect.left) // PIXEL_X
                    y = (pos[cartesian_y] - main_rect.top) // PIXEL_Y
                    if(table.validate_pice_oposite(x, y)):
                            current_pice = turn_dict[turn]
                            table.put_pice(x, y, current_pice[pice_in_game]) 
                            turn = current_pice[next_turn]
                            tie_conunter += 1; 
                                          
                    if table.validate_winner(XPice):
                        winer_img = XPICE_IMG
                        current_status = Status.WINNER
                    if table.validate_winner(OPice):
                        winer_img = OPICE_IMG
                        current_status = Status.WINNER
                    if tie_conunter == 9:
                         current_status = Status.WINNER

            if current_status == Status.MENU:
                if center_rects(WIDTH, 300) < pos[cartesian_x] and (center_rects(WIDTH, 300) < pos[cartesian_x] and pos[cartesian_y] > 90 and pos[cartesian_y] < 150 + 90 ):
                    current_status = Status.INGAME
            if current_status == Status.WINNER:
                if center_rects(WIDTH, 300) < pos[cartesian_x] and (center_rects(WIDTH, 300) < pos[cartesian_x] and pos[cartesian_y] > 90 and pos[cartesian_y] < 150 + 90 ):
                    current_status = Status.MENU


    screen.fill("purple")
    if(current_status == Status.MENU):
        tie_conunter = 0
        screen.blit(START_IMG, (center_rects(WIDTH, 300), 90))
        table = Table()

    if(current_status == Status.INGAME):
        screen.fill("blue", main_rect )
        draw_lines(main_rect,Table.SIZE, screen, table)

    if(current_status == Status.WINNER):
        screen.blit(RESTART_IMG, (center_rects(WIDTH, 300), 90))
        if(winer_img != None):
            screen.blit(WINNER_IMG, (center_rects(WIDTH, 300), 400))
            
            screen.blit(winer_img, (center_rects(WIDTH, 120), 220))
        else:
            screen.blit(TIE_IMG, (center_rects(WIDTH, 300), 400))
       

    pygame.display.flip()

    clock.tick(60) 
pygame.quit()