import osmnx as ox
import heapq

# -------------------------------------------------
# 1. Download the road network
# -------------------------------------------------

latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

# -------------------------------------------------
# 2. Start and destination
# -------------------------------------------------

start_node = 9798754060
destination_node = 7048096533

# -------------------------------------------------
# 3. Our original shortest route
# -------------------------------------------------

original_route = [
    9798754060,
    9798754061,
    9798754062,
    9798754058,
    9798754056,
    9798754075,
    9798754072,
    9798754076,
    9798754078,
    9798754080,
    6758953958,
    7018323673,
    9798617638,
    7048096536,
    7048096535,
    7048096533
]

# -------------------------------------------------
# 4. Select a road to block
# -------------------------------------------------

blocked_start = original_route[7]
blocked_end = original_route[8]

print("Blocked Road:")
print(blocked_start, "->", blocked_end)

# -------------------------------------------------
# 5. Dijkstra Algorithm
# -------------------------------------------------

def dijkstra(graph, start, destination, blocked_edge):

    distances = {
        node: float("inf")
        for node in graph.nodes
    }

    previous = {
        node: None
        for node in graph.nodes
    }

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        if current_node == destination:
            break

        if current_distance > distances[current_node]:
            continue

        for neighbor in graph.neighbors(current_node):

            # Skip blocked road
            if (
                current_node == blocked_edge[0]
                and neighbor == blocked_edge[1]
            ):
                continue

            edge_data = graph.get_edge_data(
                current_node,
                neighbor
            )

            weight = min(
                data.get("length", 1)
                for data in edge_data.values()
            )

            new_distance = (
                current_distance + weight
            )

            if new_distance < distances[neighbor]:

                distances[neighbor] = new_distance

                previous[neighbor] = current_node

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor)
                )

    # -------------------------------------------------
    # 6. Reconstruct route
    # -------------------------------------------------

    path = []

    current = destination

    while current is not None:

        path.append(current)

        current = previous[current]

    path.reverse()

    return path, distances[destination]


# -------------------------------------------------
# 7. Calculate new route
# -------------------------------------------------

new_route, new_distance = dijkstra(
    graph,
    start_node,
    destination_node,
    (blocked_start, blocked_end)
)

# -------------------------------------------------
# 8. Display result
# -------------------------------------------------

print("\nOriginal Route:")
print(original_route)

print("\nNew Route After Road Block:")
print(new_route)

print("\nOriginal Distance: 2123.06 meters")

print(
    "New Distance:",
    round(new_distance, 2),
    "meters"
)

print(
    "\nOriginal Route Nodes:",
    len(original_route)
)

print(
    "New Route Nodes:",
    len(new_route)
)