import osmnx as ox

# Same location and road network
latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=1000,
    network_type="drive"
)

# Emergency vehicle starting location
start_lat = 12.8728
start_lon = 80.2194

# Emergency destination
destination_lat = 12.8780
destination_lon = 80.2250

# Find nearest road nodes
start_node = ox.distance.nearest_nodes(
    graph,
    start_lon,
    start_lat
)

destination_node = ox.distance.nearest_nodes(
    graph,
    destination_lon,
    destination_lat
)

print("Start Node:", start_node)
print("Destination Node:", destination_node)