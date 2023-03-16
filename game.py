import sys
from os.path import dirname, join

import pygame
from pygame.time import Clock

from board import BoardRenderer
from sprites.tile import init_main_tile

ASSETS_PATH = join(dirname(__file__), 'assets')

#WINSIZE = (1280, 1024)
#WINSIZE = (400, 400)
default_size = 10


def main():
    clock = Clock()
    pygame.init()
    width = 4
    height = 5
    WINSIZE = (15*width, 24+(15*height))
    print(WINSIZE)
    screen: pygame.Surface = pygame.display.set_mode(WINSIZE)
    init_main_tile()
    sys.setrecursionlimit(2500)
    difficulty = 1

    board = BoardRenderer(WINSIZE[0], WINSIZE[1], width, height, difficulty=difficulty)
    while not board.is_finished:
        board.render(screen)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    return True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    board.handle_click(event.pos, True)
                elif event.button == 3:
                    board.handle_click(event.pos, False)
        clock.tick(30)

    while True:
        board.render(screen)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        clock.tick(30)


while main():
    main()

