import sys
import math

def wait():
    print("WAIT")

def debug(message):
    print(message, file=sys.stderr, flush=True)

class Robot:
    def __init__(self, scrap_amount):
        self.scraps = scrap_amount

class GameBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"{self.width} {self.height}"

class Score:
    def __init__(self):
        self.player = 0
        self.enemy = 0
    
    def update(self):
        self.player, self.enemy = [int(i) for i in input().split()]

    def show(self):
        debug(f"SCORE: player: {self.player}, enemy: {self.enemy}")

game_board = GameBoard(*[int(i) for i in input().split()])
score = Score()

debug(game_board)

while True:
    score.update()

    wait()
    
"""
width, height = [int(i) for i in input().split()]

# game loop
while True:
    my_matter, opp_matter = [int(i) for i in input().split()]
    for i in range(height):
        for j in range(width):
            # owner: 1 = me, 0 = foe, -1 = neutral
            scrap_amount, owner, units, recycler, can_build, can_spawn, in_range_of_recycler = [int(k) for k in input().split()]
            print(f"{i} {j} {owner} {units}", file=sys.stderr, flush=True)
    # Write an action using print
    # To debug: 
    

    print("WAIT")
"""

