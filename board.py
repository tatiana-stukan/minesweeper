from random import randint
from typing import List, Set, Union, Optional

from pygame import Surface
from pygame.draw_py import Point

from sprites.tile import FieldSprites, FaceSprites, MainTile

default_size = 10


class Field:
    def __init__(self, is_mine: bool = False, field_type: FieldSprites = FieldSprites.closed):
        self._field_type: FieldSprites = field_type
        self.is_mine = is_mine
        self.tile = MainTile.tile.fields[self.field_type.value]

    @property
    def field_type(self) -> FieldSprites:
        return self._field_type

    @field_type.setter
    def field_type(self, value: Union[FieldSprites, int]):
        if isinstance(value, FieldSprites):
            self.tile = MainTile.tile.fields[value.value]
            self._field_type = value
        elif isinstance(value, int):
            if value == 0:
                self._field_type = FieldSprites.empty
            else:
                self._field_type = FieldSprites.digit
            self.tile = MainTile.tile.digits[value]
        else:
            raise ValueError


class Board:
    def __init__(self, width: int = default_size, height: int = default_size, difficulty: int = 1):
        self.width = width
        self.height = height
        self.board: List[List[Field]] = [
            [Field() for i in range(self.width)]
            for _ in range(self.height)
        ]
        self.difficulty = difficulty
        self.mines_count: int = max(round(width * height / (9 / self.difficulty)), 3)
        self.mines: Set[Point] = set()
        self.lost: bool = False
        self.loose: bool = False

    def first_click(self, x: int, y: int):
        click_row = x
        click_column = y

        available_cells = [
            [i, j]
            for i in range(self.height)
            for j in range(self.width)
            if i not in [click_row - 1, click_row, click_row + 1] or
               j not in [click_column - 1, click_column, click_column + 1]
        ]

        used = set()
        for _ in range(self.mines_count):
            index = randint(0, len(available_cells) - 1)
            while index in used:
                index = randint(0, len(available_cells) - 1)
            used.add(index)
            row = available_cells[index][0]
            column = available_cells[index][1]
            self.board[row][column].is_mine = True
            self.mines.add((row, column))

        self.reveal(x, y)

    def set_flagged(self, x: int, y: int):
        if self.board[x][y].field_type == FieldSprites.question_mark:
            self.board[x][y].field_type = FieldSprites.closed
        elif self.board[x][y].field_type == FieldSprites.flagged:
            self.set_questioned(x, y)
        elif self.board[x][y].field_type == FieldSprites.closed:
            self.board[x][y].field_type = FieldSprites.flagged

    def set_questioned(self, x: int, y: int):
        self.board[x][y].field_type = FieldSprites.question_mark

    def game_over(self, x: int = -1, y: int = -1):
        if x == -1 or y == - 1:
            self.lost = True
        for row in range(self.height):
            for column in range(self.width):
                if row == x and column == y:
                    self.board[row][column].field_type = FieldSprites.clicked_mine
                elif self.board[row][column].field_type == FieldSprites.closed or self.board[row][
                    column].field_type == FieldSprites.question_mark:
                    if (row, column) in self.mines:
                        self.board[row][column].field_type = FieldSprites.mine
                    else:
                        self.board[row][column].field_type = self.count_mines(row, column)
                elif self.board[row][column].field_type == FieldSprites.flagged:
                    if (row, column) not in self.mines:
                        self.board[row][column].field_type = FieldSprites.crossed_mine

    def is_finished(self) -> bool:
        if self.lost:
            return True
        adjacents = [
            (0, -1), (0, 1), (-1, 0), (1, 0),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]
        for mine in self.mines:
            for adjacent in adjacents:
                cell: Field = self.get_cell(mine[0] + adjacent[0], mine[1] + adjacent[1])
                if cell is not None:
                    if (cell.field_type not in FieldSprites.digits()) and (
                            (mine[0] + adjacent[0], mine[1] + adjacent[1]) not in self.mines):
                        return False
        return True

    def get_cell(self, row, column) -> Optional[Field]:
        if row >= self.height or column >= self.width or row < 0 or column < 0:
            return
        return self.board[row][column]

    def count_mines(self, row, column) -> int:
        adjacents = [
            (0, -1), (0, 1), (-1, 0), (1, 0),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]
        counter = 0
        for adjacent in adjacents:
            cell: Field = self.get_cell(row + adjacent[0], column + adjacent[1])
            if cell is not None:
                if cell.is_mine:
                    counter += 1
        return counter

    def reveal(self, x: int, y: int):
        if (
                self.board[x][y].field_type == FieldSprites.flagged or
                self.board[x][y].field_type == FieldSprites.question_mark
        ):
            return

        adjacents = [
            (0, -1), (0, 1), (-1, 0), (1, 0),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]

        def reveal(row, column):
            cell: Field = self.get_cell(row, column)
            if cell is None:
                return
            if cell.field_type in FieldSprites.digits():
                return
            if cell.is_mine:
                return

            self.board[row][column].field_type = self.count_mines(row, column)
            if self.board[row][column].field_type != FieldSprites.empty:
                return

            for direction in adjacents:
                reveal(row + direction[0], column + direction[1])

        if self.board[x][y].is_mine:
            self.loose = True
            self.game_over(x, y)

            return

        reveal(x, y)


class BoardRenderer:
    def __init__(self,
                 screen_width: int, screen_height: int,
                 board_width: int = default_size, board_height: int = default_size, difficulty: int = 1):
        self.board: Board = Board(board_width, board_height, difficulty=difficulty)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.board_width = MainTile.tile.sprite_size * board_width
        self.board_height = MainTile.tile.sprite_size * board_height

        self.offset_x = round(self.screen_width / 2 - self.board_width / 2)
        self.offset_y = round(self.screen_height / 2 - (self.board_height - 24) / 2)
        print(self.offset_x, self.offset_y)
        self.offset_face_x = round(self.screen_width / 2) - 12
        self.offset_face_y = 0
        self.is_finished = False
        self.initialized: bool = False

    def handle_click(self, position, left: bool = True):
        if self.is_finished:
            return

        x, y = position
        if x < self.offset_x or x > self.offset_x + self.board_width:
            return
        if y < self.offset_y or y > self.offset_y + self.board_height:
            return

        row = (y - self.offset_y) // MainTile.tile.sprite_size
        column = (x - self.offset_x) // MainTile.tile.sprite_size
        if not self.initialized and not left:
            self.board.set_flagged(row, column)
            return
        if self.initialized:
            if left:
                self.board.reveal(row, column)
            else:
                self.board.set_flagged(row, column)
        elif left:
            self.board.first_click(row, column)
            self.initialized = True
        self.is_finished = self.board.is_finished()
        if self.is_finished:
            self.board.game_over()

    def render(self, screen: Surface):
        dy = self.offset_y
        for row in range(self.board.height):
            dx = self.offset_x
            for column in range(self.board.width):
                screen.blit(
                    self.board.board[row][column].tile,
                    (dx, dy)
                )
                dx += MainTile.tile.sprite_size
            dy += MainTile.tile.sprite_size
        dy = self.offset_face_y
        dx = self.offset_face_x
        if not self.is_finished:
            screen.blit(MainTile.tile.faces[FaceSprites.usual.value], (dx, dy))
        elif self.board.loose:
            screen.blit(MainTile.tile.faces[FaceSprites.dead.value], (dx, dy))
        else:
            screen.blit(MainTile.tile.faces[FaceSprites.win.value], (dx, dy))


