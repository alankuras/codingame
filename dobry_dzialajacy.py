import sys
import math
from typing import List
from itertools import chain
from pandas import DataFrame
import random
from enum import Enum
from dataclasses import dataclass
from scipy import spatial
import numpy as np


class Owner(Enum):
    PLAYER = 1
    ENEMY = 0
    NEUTRAL = -1
    UNKNOWN = -100


class StartingPosition(Enum):
    RIGHT = 1
    LEFT = 0


class POSITION(Enum):
    # (h, w)
    TOP = (1, 0)
    TOP_LEFT = (1, -1)
    TOP_RIGHT = (1, 1)
    LEFT = (0, -1)
    RIGHT = (0, 1)
    BOTTOM = (-1, 0)
    BOTTOM_LEFT = (-1, -1)
    BOTTOM_RIGHT = (-1, 1)


class Tile:
    def __init__(self, h, w, scrap_amount, owner, units, recycler, can_build, can_spawn, in_range_of_recycler):
        self.h = h
        self.w = w
        self.scrap_amount = int(scrap_amount)
        self.owner = Owner(int(owner))
        self.units = int(units)
        self.recycler = True if int(recycler) == 1 else False
        self.can_build = True if int(can_build) == 1 else False
        self.can_spawn = True if int(can_spawn) == 1 else False
        self.in_range_of_recycler = True if int(in_range_of_recycler) == 1 else False

    def __repr__(self):
        return f"{self.h} {self.w} {self.owner} {self.units} {self.h} {self.w}"

    @property
    def is_not_green(self):
        return self.scrap_amount > 0

    @property
    def has_units(self):
        return self.units > 0


class GameBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile(0, 0, 0, 0, 0, 0, 0, 0, 0) for w in range(width)] for h in range(height)]
        self._starting_position = None
        self.recyclers_spawned = 0
        self._spawn_point = (0, 0)
        self._top_sentinel = (0, 0)
        self._bottom_sentinel = (0, 0)

    @property
    def recyclers(self):
        return len([x for x in chain.from_iterable(self.tiles) if x.recycler and x.owner == Owner.PLAYER])

    def h_exists(self, h):
        return 0 <= h < self.height

    def w_exists(self, w):
        return 0 <= w < self.width

    def tile_on_board(self, h, w):
        return self.h_exists(h) and self.w_exists(w)

    def update_field(self):
        for h in range(self.height):
            for w in range(self.width):
                self.tiles[h][w] = Tile(h, w, *[k for k in input().split()])  # type: ignore

    def get_tiles(self, unit_owner: Owner = Owner.UNKNOWN):
        if unit_owner == Owner.UNKNOWN:
            return [x for x in chain.from_iterable(self.tiles)]
        else:
            return [x for x in chain.from_iterable(self.tiles) if x.owner == unit_owner]

    def get_player_tiles_with_units(self, unit_owner: Owner = Owner.PLAYER):
        return [x for x in chain.from_iterable(self.tiles) if x.owner == unit_owner and x.has_units]

    def get_orphan_tiles(self, unit_owner: Owner = Owner.PLAYER):
        return [x for x in chain.from_iterable(self.tiles) if
                x.owner in [Owner.NEUTRAL, Owner.ENEMY] and x.is_not_green]

    def find_tiles(self, h, w):
        return self.tiles[h][w]

    @property
    def starting_position(self):
        if self._starting_position is None:
            self._starting_position = StartingPosition(
                max(self.get_tiles(Owner.PLAYER), key=lambda x: x.w).w > self.width / 2)
            self._spawn_point = [x for x in self.get_tiles(Owner.PLAYER) if x.units == 0][0]
            self._top_sentinel = [x for x in self.get_tiles(Owner.PLAYER) if x.units > 0][0]
            self._bottom_sentinel = [x for x in self.get_tiles(Owner.PLAYER) if x.units > 0][-1]
        return self._starting_position


class Score:
    def __init__(self):
        self.player = 0
        self.enemy = 0
        self.turn = 0

    def update(self):
        self.turn += 1
        self.player, self.enemy = [int(i) for i in input().split()]

    def __repr__(self):
        return (f"SCORE: player: {self.player}, enemy: {self.enemy}")


class Actions:
    def __init__(self, debug_on=False):
        self.actions = []
        self.debug_on = debug_on

    def wait(self):
        print(';'.join(self.actions) if len(self.actions) > 0 else 'WAIT')

    def message(self, message):
        self.actions.append(f"MESSAGE {message}")

    def debug(self, message):
        if self.debug_on:
            print(message, file=sys.stderr, flush=True)

    def spawn(self, tile: Tile, no_units: int = 1):
        self.actions.append((f"SPAWN {no_units} {tile.w} {tile.h}"))

    def move(self, tile: Tile, to_h, to_w, no_units: int = 1):
        self.actions.append((f"MOVE {no_units} {tile.w} {tile.h} {to_w} {to_h}"))

    def build(self, tile: Tile):
        self.actions.append((f"BUILD {tile.w} {tile.h}"))

    def move_to(self, tile: Tile, position: POSITION, no_units: int = 1):
        self.actions.append(
            (f"MOVE {no_units} {tile.w} {tile.h} {tile.w + position.value[0]} {tile.h + position.value[0]}"))


class Strategies:
    def __init__(self):
        self._strategy_sets = []

    def spawn_units_randomly(self, game_board: GameBoard, actions: Actions):
        for unit in range(score.player // 10):
            tile = random.choice(game_board.get_tiles(unit_owner=Owner.PLAYER))
            if tile.can_spawn:
                actions.spawn(tile=tile, no_units=1)

    def spawn_units_right(self, game_board: GameBoard, actions: Actions):
        tiles = sorted([x for x in game_board.get_tiles(Owner.PLAYER) if x.units == 0], key=lambda x: x.w, reverse=True)
        for tile in tiles:
            if tile.can_spawn and score.player >= 10:
                actions.spawn(tile=tile, no_units=1)
                score.player -= 10

    def spawn_units_left(self, game_board: GameBoard, actions: Actions):
        tiles = sorted([x for x in game_board.get_tiles(Owner.PLAYER) if x.units == 0], key=lambda x: x.w,
                       reverse=False)
        for tile in tiles:
            if tile.can_spawn and score.player >= 10:
                actions.spawn(tile=tile, no_units=1)
                score.player -= 10

    def increase_units_randomly(self, game_board: GameBoard, actions: Actions):
        for unit in range(score.player // 10):
            tile = random.choice(
                [x for x in game_board.get_tiles(unit_owner=Owner.PLAYER) if x.units > 0 and not x.recycler])
            if tile.can_spawn:
                actions.spawn(tile=tile, no_units=1)

    def spawn_units_near_enemies(self, game_board: GameBoard, actions: Actions):
        for tile in game_board.get_tiles(Owner.PLAYER):
            if tile.can_spawn:
                pos = (tile.h + 1, tile.w)
                pos2 = (tile.h - 1, tile.w)
                pos3 = (tile.h, tile.w + 1)
                pos4 = (tile.h, tile.w - 1)

                if game_board.tile_on_board(*pos) and game_board.find_tiles(
                        *pos).owner == Owner.ENEMY and game_board.find_tiles(
                    *pos).has_units and not game_board.find_tiles(*pos).recycler:
                    actions.spawn(tile=tile, no_units=1)
                    continue
                elif game_board.tile_on_board(*pos2) and game_board.find_tiles(
                        *pos2).owner == Owner.ENEMY and game_board.find_tiles(
                    *pos2).has_units and not game_board.find_tiles(*pos2).recycler:
                    actions.spawn(tile=tile, no_units=1)
                    continue
                elif game_board.tile_on_board(*pos3) and game_board.find_tiles(
                        *pos3).owner == Owner.ENEMY and game_board.find_tiles(
                    *pos3).has_units and not game_board.find_tiles(*pos3).recycler:
                    actions.spawn(tile=tile, no_units=1)
                    continue
                elif game_board.tile_on_board(*pos4) and game_board.find_tiles(
                        *pos4).owner == Owner.ENEMY and game_board.find_tiles(
                    *pos4).has_units and not game_board.find_tiles(*pos4).recycler:
                    actions.spawn(tile=tile, no_units=1)
                    continue

    def _check_and_move(self, tile: Tile, to_h, to_w, game_board: GameBoard, actions: Actions,
                        compare_units_count=False):
        if compare_units_count:
            if game_board.tile_on_board(to_h, to_w) and game_board.tiles[to_h][
                to_w].owner != Owner.PLAYER and tile.units >= \
                    game_board.tiles[to_h][to_w].units:
                actions.move(tile, to_h, to_w, no_units=tile.units)
                return True
            return False
        else:
            if game_board.tile_on_board(to_h, to_w) and game_board.tiles[to_h][to_w].owner != Owner.PLAYER:
                actions.move(tile, to_h, to_w, no_units=1)
                return True
            return False

    def _check_and_move_to(self, tile: Tile, position: POSITION, game_board: GameBoard, actions: Actions):
        to_h = tile.h + position.value[0]
        to_w = tile.w + position.value[1]
        if game_board.tile_on_board(to_h, to_w) and game_board.tiles[to_h][
            to_w].owner != Owner.PLAYER and not tile.recycler and game_board.tiles[to_h][to_w].is_not_green and \
                game_board.tiles[to_h][to_w].units <= tile.units:
            actions.move(tile, to_h, to_w, no_units=1)
            game_board.tiles[to_h][to_w].owner = Owner.PLAYER
            return True
        return False

    def go_to_far_left(self, game_board: GameBoard, actions: Actions):
        for tile in game_board.get_player_tiles_with_units():
            for unit in range(tile.units):
                if self._check_and_move_to(tile, POSITION.LEFT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP_RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP_LEFT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM_RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM_LEFT, game_board=game_board, actions=actions):
                    continue
                self.find_something_on_the_board(game_board=game_board, actions=actions, tile=tile)
        self.spawn_units_left(game_board=game_board, actions=actions)

    def go_to_far_right(self, game_board: GameBoard, actions: Actions):
        for tile in game_board.get_player_tiles_with_units():
            for unit in range(tile.units):
                if self._check_and_move_to(tile, POSITION.RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.LEFT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP_RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.TOP_LEFT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM_RIGHT, game_board=game_board, actions=actions):
                    continue
                elif self._check_and_move_to(tile, POSITION.BOTTOM_LEFT, game_board=game_board, actions=actions):
                    continue
                self.find_something_on_the_board(game_board=game_board, actions=actions, tile=tile)
        self.spawn_units_right(game_board=game_board, actions=actions)

    def go_to_the_edge(self, game_board: GameBoard, actions: Actions):
        if game_board.starting_position == StartingPosition.LEFT:
            self.go_to_far_right(game_board=game_board, actions=actions)
        else:
            self.go_to_far_left(game_board=game_board, actions=actions)

    def build_recycler_when_near_enemy_fields(self, game_board: GameBoard, actions: Actions, max_recyclers=10):
        if game_board.recyclers < max_recyclers:
            for tile in game_board.get_tiles(Owner.PLAYER):
                if tile.can_build and not tile.recycler:
                    pos = (tile.h + 1, tile.w)
                    pos2 = (tile.h - 1, tile.w)
                    pos3 = (tile.h, tile.w + 1)
                    pos4 = (tile.h, tile.w - 1)

                    if game_board.tile_on_board(*pos) and game_board.find_tiles(*pos).owner == Owner.ENEMY:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos2) and game_board.find_tiles(*pos2).owner == Owner.ENEMY:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos3) and game_board.find_tiles(*pos3).owner == Owner.ENEMY:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos4) and game_board.find_tiles(*pos4).owner == Owner.ENEMY:
                        actions.build(tile)
                        continue

    def build_recycler_when_spotted_units(self, game_board: GameBoard, actions: Actions, max_recyclers=10):
        if game_board.recyclers < max_recyclers:
            for tile in game_board.get_tiles(Owner.PLAYER):
                if tile.can_build:
                    pos = (tile.h + 1, tile.w)
                    pos2 = (tile.h - 1, tile.w)
                    pos3 = (tile.h, tile.w + 1)
                    pos4 = (tile.h, tile.w - 1)

                    if game_board.tile_on_board(*pos) and game_board.find_tiles(
                            *pos).owner == Owner.ENEMY and game_board.find_tiles(*pos).has_units:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos2) and game_board.find_tiles(
                            *pos2).owner == Owner.ENEMY and game_board.find_tiles(*pos2).has_units:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos3) and game_board.find_tiles(
                            *pos3).owner == Owner.ENEMY and game_board.find_tiles(*pos3).has_units:
                        actions.build(tile)
                        continue
                    elif game_board.tile_on_board(*pos4) and game_board.find_tiles(
                            *pos4).owner == Owner.ENEMY and game_board.find_tiles(*pos4).has_units:
                        actions.build(tile)
                        continue

    def free_hunt(self, game_board: GameBoard, actions: Actions):
        for tile in game_board.get_player_tiles_with_units():
            for t in game_board.get_player_tiles_with_units(Owner.ENEMY):
                actions.spawn(tile=tile, no_units=1)
                actions.move(tile, t.h, t.w, tile.units)

    def take_closest(self, game_board: GameBoard, actions: Actions):
        for tile in game_board.get_player_tiles_with_units():
            moved = False
            for enemy_tile in [x for x in game_board.get_orphan_tiles() if
                               abs(tile.w - x.w) < 2 and abs(tile.h - x.h) < 2]:
                actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                moved = True
                break
            if not moved:
                for enemy_tile in [x for x in game_board.get_orphan_tiles() if
                                   abs(tile.w - x.w) < 3 and abs(tile.h - x.h) < 3]:
                    actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                    moved = True
                    break
            if not moved:
                for enemy_tile in [x for x in game_board.get_orphan_tiles() if
                                   abs(tile.w - x.w) < 4 and abs(tile.h - x.h) < 4]:
                    actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                    moved = True
                    break
            if not moved:
                for enemy_tile in [x for x in game_board.get_orphan_tiles() if
                                   abs(tile.w - x.w) < 5 and abs(tile.h - x.h) < 5]:
                    actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                    moved = True
                    break
            if not moved:
                for enemy_tile in [x for x in game_board.get_orphan_tiles() if
                                   abs(tile.w - x.w) < 6 and abs(tile.h - x.h) < 6]:
                    actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                    moved = True
                    break
            if not moved:
                for enemy_tile in game_board.get_orphan_tiles():
                    actions.move(tile, enemy_tile.h, enemy_tile.w, tile.units)
                    moved = True
                    break

    def find_something_on_the_board(self, game_board: GameBoard, actions: Actions, tile: Tile):
        for t in game_board.get_tiles(Owner.ENEMY):
            actions.move(tile=tile, to_h=t.h, to_w=t.w)
            break

    def activate_top_sentinel(self, game_board: GameBoard, actions: Actions):
        sentinel = game_board._top_sentinel
        if sentinel.h > 0:  # type: ignore
            # actions.debug(f"SENTINEL ACTIVE")
            if sentinel.h - 2 > 0:
                actions.move(tile=sentinel, to_h=sentinel.h - 2, to_w=sentinel.w)  # type: ignore
            else:
                actions.move(tile=sentinel, to_h=sentinel.h - 1, to_w=sentinel.w)
            actions.spawn(sentinel, 1)  # type: ignore
            sentinel.h = sentinel.h - 1  # type: ignore

    def activate_bottom_sentinel(self, game_board: GameBoard, actions: Actions):
        sentinel = game_board._bottom_sentinel
        if sentinel.h < game_board.height:  # type: ignore
            # actions.debug(f"SENTINEL ACTIVE")
            actions.spawn(sentinel, 1)
            actions.move(tile=sentinel, to_h=sentinel.h + 2, to_w=sentinel.w)  # type: ignore
            sentinel.h = sentinel.h + 1  # type: ignore

    def fill_bottom_with_units(self, game_board: GameBoard, actions: Actions):
        for tile in [x for x in game_board.get_tiles(Owner.PLAYER) if not x.recycler and x.units == 0][::-1]:
            if score.player >= 10:
                actions.spawn(tile=tile, no_units=1)
                break


game_board = GameBoard(*[int(i) for i in input().split()])
score = Score()
strategies = Strategies()

while True:
    actions = Actions(debug_on=True)
    score.update()
    game_board.update_field()
    game_board.starting_position
    if score.turn < game_board.width:
        # actions.message(message="PHASE 1")
        strategies.activate_top_sentinel(game_board=game_board, actions=actions)
        strategies.activate_bottom_sentinel(game_board=game_board, actions=actions)  # wywalic go tp ?
        strategies.spawn_units_near_enemies(game_board=game_board, actions=actions)
        strategies.build_recycler_when_spotted_units(game_board=game_board, actions=actions, max_recyclers=10)
        strategies.go_to_the_edge(game_board=game_board, actions=actions)
        """
        if score.turn < 2:
            for tile in [x for x in game_board.get_tiles(Owner.PLAYER) if x.can_build]:
                actions.build(tile)
                break
        strategies.fill_bottom_with_units(game_board=game_board, actions=actions)
        """
    else:
        # actions.message(message="PHASE 2")
        strategies.take_closest(game_board=game_board, actions=actions)
        strategies.build_recycler_when_spotted_units(game_board=game_board, actions=actions, max_recyclers=15)
        strategies.spawn_units_near_enemies(game_board=game_board, actions=actions)
        strategies.spawn_units_randomly(game_board=game_board, actions=actions)

        # strategies.free_hunt(game_board=game_board, actions=actions)

    actions.wait()
