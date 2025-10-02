import pygame
import enum


class Status(enum.Enum):
      INGAME = enum.auto()
      WINNER = enum.auto()
      MENU = enum.auto()
def center_rects(container_size, object_size) -> int:

    return (container_size//2) - (object_size//2) 


def draw_lines(rect,  table_size, screen, table) :
    x_init_pos = rect.left
    y_init_pos = rect.top
    y_final_pos = rect.height + y_init_pos
    x_final_pos = rect.width  + x_init_pos
    x_pixel = round(rect.width/ table_size)
    y_pixel = round(rect.height / table_size)

    for  x in range(x_init_pos, x_final_pos, x_pixel):
          pygame.draw.line(screen, "black", (x, y_init_pos), (x, y_final_pos), 5)
          
    for  y in range(y_init_pos, y_final_pos, y_pixel):
          pygame.draw.line(screen, "black", (x_init_pos, y), (x_final_pos, y ), 5)
    for  x in range(x_init_pos, x_final_pos, x_pixel):
            for  y in range(y_init_pos, y_final_pos, x_pixel):
                  #main_rect = pygame.Rect(x + 22, y+22 , 120,120)
                 x_pos = (x - x_init_pos) // x_pixel  
                 y_pos = (y - y_init_pos) // y_pixel

                 #x_pos = (x // x_pixel) - 1  
                 #y_pos = (y // y_pixel) - 1 
                  
                 if( table.validate_pice(x_pos, y_pos) ):
                        screen.blit(table.get_image(x_pos, y_pos), (x + 22, y+22))
                  #screen.fill("purple", main_rect)