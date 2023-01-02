from collections import deque
from typing import List
graph = {
    "A": ["B", "C"],
    "B": ["C", "I"],
    "C": ["A", "B", "D", "I"],
    "D": ["E", "C", "F"],
    "E": ["D"],
    "F": ["D", "G"],
    "G": ["F", "H", "I"],
    "I": ["A", "B", "C"]
}


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


print(search(graph=graph, root="B", node_to_find="H"))
