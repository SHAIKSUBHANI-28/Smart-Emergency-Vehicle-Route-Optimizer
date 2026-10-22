import osmnx as ox
import matplotlib.pyplot as plt

# Road network
latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

# Dijkstra shortest route
route = [
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

# Calculate total distance
total_distance = 0

for i in range(len(route) - 1):

    edge_data = graph.get_edge_data(
        route[i],
        route[i + 1]
    )

    distance = min(
        data.get("length", 0)
        for data in edge_data.values()
    )

    total_distance += distance

# Estimated time
average_speed = 30  # km/hour

time_hours = (total_distance / 1000) / average_speed
time_minutes = time_hours * 60

# Get route coordinates
route_x = []
route_y = []

for node in route:

    route_x.append(graph.nodes[node]["x"])
    route_y.append(graph.nodes[node]["y"])

# Plot road network
fig, ax = ox.plot_graph(
    graph,
    show=False,
    close=False,
    figsize=(10, 10)
)

# Draw shortest route
ax.plot(
    route_x,
    route_y,
    linewidth=5
)

# Start marker
ax.scatter(
    route_x[0],
    route_y[0],
    s=150,
    marker="o",
    zorder=5
)

# Destination marker
ax.scatter(
    route_x[-1],
    route_y[-1],
    s=180,
    marker="X",
    zorder=5
)

# Title
ax.set_title(
    "Smart Emergency Vehicle Route Optimizer",
    fontsize=16
)

# Display information
ax.text(
    0.02,
    0.02,
    f"Shortest Distance: {total_distance / 1000:.2f} km\n"
    f"Estimated Time: {time_minutes:.1f} minutes\n"
    f"Route Nodes: {len(route)}",
    transform=ax.transAxes,
    fontsize=12,
    bbox=dict(facecolor="white", alpha=0.8)
)

plt.show()