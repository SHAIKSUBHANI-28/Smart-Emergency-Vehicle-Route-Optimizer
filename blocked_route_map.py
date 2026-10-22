import osmnx as ox
import matplotlib.pyplot as plt

# -------------------------------------------------
# 1. Download road network
# -------------------------------------------------

latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

# -------------------------------------------------
# 2. Original route
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
# 3. New route after road block
# -------------------------------------------------

new_route = [
    9798754060,
    9798754061,
    9798754062,
    9798754058,
    9798754067,
    7768923099,
    6768830229,
    9798754017,
    13352865756,
    13352925713,
    7018323673,
    9798617638,
    7048096536,
    7048096535,
    7048096533
]

# -------------------------------------------------
# 4. Blocked road
# -------------------------------------------------

blocked_start = 9798754076
blocked_end = 9798754078

# -------------------------------------------------
# 5. Function to get coordinates
# -------------------------------------------------

def get_coordinates(route):

    x = []
    y = []

    for node in route:

        x.append(graph.nodes[node]["x"])
        y.append(graph.nodes[node]["y"])

    return x, y


# Original route coordinates
original_x, original_y = get_coordinates(
    original_route
)

# New route coordinates
new_x, new_y = get_coordinates(
    new_route
)

# Blocked road coordinates
blocked_x = [
    graph.nodes[blocked_start]["x"],
    graph.nodes[blocked_end]["x"]
]

blocked_y = [
    graph.nodes[blocked_start]["y"],
    graph.nodes[blocked_end]["y"]
]

# -------------------------------------------------
# 6. Plot complete road network
# -------------------------------------------------

fig, ax = ox.plot_graph(
    graph,
    show=False,
    close=False,
    figsize=(12, 10)
)

# -------------------------------------------------
# 7. Original shortest route
# -------------------------------------------------

ax.plot(
    original_x,
    original_y,
    linewidth=5,
    label="Original Shortest Route"
)

# -------------------------------------------------
# 8. New route after blockage
# -------------------------------------------------

ax.plot(
    new_x,
    new_y,
    linewidth=5,
    linestyle="--",
    label="Alternative Route"
)

# -------------------------------------------------
# 9. Blocked road
# -------------------------------------------------

ax.plot(
    blocked_x,
    blocked_y,
    linewidth=8,
    linestyle=":",
    label="Blocked Road"
)

# -------------------------------------------------
# 10. Start marker
# -------------------------------------------------

ax.scatter(
    original_x[0],
    original_y[0],
    s=200,
    marker="o",
    zorder=5
)

# -------------------------------------------------
# 11. Destination marker
# -------------------------------------------------

ax.scatter(
    original_x[-1],
    original_y[-1],
    s=250,
    marker="X",
    zorder=5
)

# -------------------------------------------------
# 12. Title
# -------------------------------------------------

ax.set_title(
    "Smart Emergency Vehicle Route Optimizer\n"
    "Dynamic Rerouting After Road Block",
    fontsize=16
)

# -------------------------------------------------
# 13. Information
# -------------------------------------------------

ax.text(
    0.02,
    0.02,
    "Original Distance: 2.12 km\n"
    "New Distance: 2.21 km\n"
    "Road Block: Simulated",
    transform=ax.transAxes,
    fontsize=12,
    bbox=dict(
        facecolor="white",
        alpha=0.85
    )
)

ax.legend()

plt.show()