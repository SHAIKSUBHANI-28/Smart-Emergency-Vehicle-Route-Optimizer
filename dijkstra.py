import heapq

def dijkstra(graph, start, destination):

    distances = {node: float('inf') for node in graph}
    previous = {node: None for node in graph}

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node == destination:
            break

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node].items():

            distance = current_distance + weight

            if distance < distances[neighbor]:

                distances[neighbor] = distance
                previous[neighbor] = current_node

                heapq.heappush(
                    priority_queue,
                    (distance, neighbor)
                )

    # Reconstruct the shortest path
    path = []
    current = destination

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    return path, distances[destination]


# Example road network
graph = {
    "A": {"B": 4, "C": 2},
    "B": {"A": 4, "D": 3},
    "C": {"A": 2, "D": 1},
    "D": {"B": 3, "C": 1}
}


# Find shortest route
path, distance = dijkstra(graph, "A", "D")

print("Shortest Path:", path)
print("Shortest Distance:", distance)