import osmnx as ox

latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

print("Number of nodes:", len(graph.nodes))
print("Number of roads:", len(graph.edges))

ox.plot_graph(graph)