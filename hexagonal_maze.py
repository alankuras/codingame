from collections import deque
from typing import List

class Point:
    def __init__(self, h:int , w:int) -> None:
        self.h = h
        self.w = w
    
    def __eq__(self, other):
        return (self.h, self.w) == other

    def __hash__(self):
        return hash((self.h, self.w))

    def __iter__(self):
        yield (self.h, self.w)
    
    def __repr__(self):
        return f"({self.h, self.w})"

width = 5
height = 6

matrix = [
    ['#','#','#','#','#'],
    ['#','S','#','E','#'],
    ['#','_','#','_','#'],
    ['#','_','#','_','#'],
    ['#','_','_','_','#'],
    ['#','#','#','#','#']
]

start = None
end = None
wall="#"
for h in range(height):
    for w in range(width):
        if matrix[h][w] == 'S':
            start = Point(h,w)
        elif matrix[h][w] == 'E':
            end = Point(h,w)


def find_node_edges(h,w):
    edges = []
    edges_to_check = [(h-1, w), (h+1, w), (h, w-1), (h, w+1)]
    for _h,_w in [x for x in edges_to_check]:
        if _h<0:
            _h=height-1
        elif _h>height-1:
            _h=0
        if _w<0:
            _w=width-1
        elif _w>width-1:
            _w=0
        if matrix[_h][_w] != wall:
            edges.append(Point(_h,_w))
    return edges

graph = {}
for h in range(height):
    for w in range(width):
        if matrix[h][w]!="#":
            graph[Point(h,w)] = find_node_edges(h,w)


def get_parents_for_path(parent, root, parents) -> List:
    path = [parent]
    while parent != root:
        parent = parents[parent]
        path.append(parent)
    return path[::-1]


def search(graph: dict, root, node_to_find) -> List:
    parents = {}
    q = deque(root)
    visited = [root]

    while q:
        node = q.popleft()
        if node == node_to_find:
            return get_parents_for_path(node, root, parents=parents)

        for edge in graph[node]:
            if edge not in visited:
                visited.append(edge)
                parents[edge] = node
            q.append(edge)
    return []



print("\n".join([str(x) for x in matrix]))

#for key,value in graph.items():
#    print(f"{key}: {value}")

print(search(graph=graph, root=start, node_to_find=end))
