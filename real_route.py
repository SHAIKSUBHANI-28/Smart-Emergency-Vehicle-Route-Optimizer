import osmnx as ox
import heapq

# -------------------------------------------------
# 1. Download the same road network
# -------------------------------------------------

latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

# -------------------------------------------------
# 2. Start and destination nodes
# -------------------------------------------------

start_node = 9798754060
destination_node = 7048096533

# -------------------------------------------------
# 3. Our Dijkstra Algorithm
# -------------------------------------------------

def dijkstra(graph, start, destination):

    distances = {node: float("inf") for node in graph.nodes}
    previous = {node: None for node in graph.nodes}

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node == destination:
            break

        if current_distance > distances[current_node]:
            continue

        for neighbor in graph.neighbors(current_node):

            edge_data = graph.get_edge_data(
                current_node,
                neighbor
            )

            # Use the shortest edge if multiple edges exist
            weight = min(
                data.get("length", 1)
                for data in edge_data.values()
            )

            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:

                distances[neighbor] = new_distance
                previous[neighbor] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor)
                )

    # -------------------------------------------------
    # 4. Reconstruct the shortest path
    # -------------------------------------------------

    path = []
    current = destination

    while current is not None:

        path.append(current)
        current = previous[current]

    path.reverse()

    return path, distances[destination]


# -------------------------------------------------
# 5. Find the emergency route
# -------------------------------------------------

path, distance = dijkstra(
    graph,
    start_node,
    destination_node
)

print("Shortest Route:")
print(path)

print("\nTotal Distance:")
print(round(distance, 2), "meters")

print("\nNumber of Nodes in Route:")
print(len(path))