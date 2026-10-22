from flask import Flask, render_template, jsonify, request
import osmnx as ox
import networkx as nx
import sqlite3
import os
from geopy.geocoders import Nominatim

app = Flask(__name__)
# =====================================================
# 🗄️ PHASE 7 - DATABASE SETUP
# =====================================================

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "emergency_routes.db"
)


def init_database():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_incidents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,

            destination TEXT NOT NULL,

            vehicle_type TEXT,

            distance REAL,

            travel_time INTEGER,

            route_type TEXT,

            status TEXT,

            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    """)

    connection.commit()

    connection.close()

    print(
        "🗄️ Database initialized successfully"
    )


init_database()

# =====================================================
# LOAD ROAD NETWORK
# =====================================================

latitude = 12.8728
longitude = 80.2194

graph = ox.graph_from_point(
    (latitude, longitude),
    dist=2000,
    network_type="drive"
)


# =====================================================
# ADD REAL ROAD SPEED + TRAVEL TIME
# =====================================================

graph = ox.routing.add_edge_speeds(graph)
graph = ox.routing.add_edge_travel_times(graph)


# =====================================================
# START LOCATION
# =====================================================

start_lat = 12.8728
start_lon = 80.2194


# =====================================================
# DESTINATION
# =====================================================

destination_lat = 12.8810
destination_lon = 80.2300


# =====================================================
# FIND START AND DESTINATION NODES
# =====================================================

def get_start_destination(current_graph):

    start_node = ox.distance.nearest_nodes(
        current_graph,
        start_lon,
        start_lat
    )

    destination_node = ox.distance.nearest_nodes(
        current_graph,
        destination_lon,
        destination_lat
    )

    return start_node, destination_node


# =====================================================
# CALCULATE ROUTE DISTANCE
# =====================================================

def calculate_distance(current_graph, route):

    total_distance = 0

    for i in range(len(route) - 1):

        node_a = route[i]
        node_b = route[i + 1]

        edge_data = current_graph.get_edge_data(
            node_a,
            node_b
        )

        if edge_data is None:
            continue

        # Handle MultiDiGraph
        if isinstance(edge_data, dict) and all(
            isinstance(v, dict)
            for v in edge_data.values()
        ):

            edge = min(
                edge_data.values(),
                key=lambda x: x.get(
                    "length",
                    float("inf")
                )
            )

        # Handle normal DiGraph
        else:

            edge = edge_data

        total_distance += edge.get(
            "length",
            0
        )

    return total_distance


# =====================================================
# CALCULATE ROUTE TRAVEL TIME
# =====================================================

def calculate_travel_time(current_graph, route):

    total_time = 0

    for i in range(len(route) - 1):

        node_a = route[i]
        node_b = route[i + 1]

        edge_data = current_graph.get_edge_data(
            node_a,
            node_b
        )

        if edge_data is None:
            continue

        # Handle MultiDiGraph
        if isinstance(edge_data, dict) and all(
            isinstance(v, dict)
            for v in edge_data.values()
        ):

            edge = min(
                edge_data.values(),
                key=lambda x: x.get(
                    "travel_time",
                    float("inf")
                )
            )

        # Handle normal DiGraph
        else:

            edge = edge_data

        total_time += edge.get(
            "travel_time",
            0
        )

    return total_time


# =====================================================
# CONVERT ROUTE TO COORDINATES
# =====================================================

def route_to_coordinates(current_graph, route):

    route_coordinates = []

    for node in route:

        lat = current_graph.nodes[node]["y"]
        lon = current_graph.nodes[node]["x"]

        route_coordinates.append(
            [lat, lon]
        )

    return route_coordinates


# =====================================================
# CALCULATE COMPLETE ROUTE INFORMATION
# =====================================================

def calculate_route_info(current_graph):

    start_node, destination_node = get_start_destination(
        current_graph
    )

    # ---------------------------------------------
    # Shortest distance route
    # ---------------------------------------------

    route = nx.shortest_path(
        current_graph,
        start_node,
        destination_node,
        weight="length"
    )

    distance_meters = calculate_distance(
        current_graph,
        route
    )

    travel_time_seconds = calculate_travel_time(
        current_graph,
        route
    )

    distance_km = distance_meters / 1000
    # ============================================
    # 🚑 EMERGENCY VEHICLE TRAVEL TIME
    # ============================================ 
    emergency_speed_kmh = 40

    time_minutes = max(
        1,
        round(
            (distance_km / emergency_speed_kmh) * 60
        )
    )

    route_coordinates = route_to_coordinates(
        current_graph,
        route
    )

    return (
        route_coordinates,
        distance_km,
        time_minutes,
        route
    )


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    try:

        (
            route_coordinates,
            distance_km,
            time_minutes,
            route
        ) = calculate_route_info(graph)

    except nx.NetworkXNoPath:

        return (
            "No road path found between "
            "start and destination."
        )

    return render_template(
        "index.html",

        route=route_coordinates,

        distance=round(
            distance_km,
            2
        ),

        time=time_minutes,

        alternate=False,

        original_distance=round(
            distance_km,
            2
        ),

        original_time=time_minutes,

        alternate_distance=None,

        alternate_time=None,

        recommended_route="Original Route"
    )

# =====================================================
# 📍 FIND ROUTE FROM USER SOURCE AND DESTINATION
# =====================================================



@app.route("/find-route", methods=["POST"])
def find_route():

    global graph
    global start_lat
    global start_lon
    global destination_lat
    global destination_lon

    try:

        data = request.get_json()

        source = data.get("source", "").strip()
        destination = data.get("destination", "").strip()

        if source == "" or destination == "":
            return jsonify({
                "success": False,
                "message": "Please enter both source and destination."
            })

        # ============================================
        # GEOCODING
        # ============================================

        geolocator = Nominatim(
            user_agent="smart-emergency-route-optimizer"
        )

        # ============================================
        # SOURCE COORDINATES
        # ============================================

        if source.lower() == "sathyabama institute":

            start_lat = 12.8735
            start_lon = 80.2205

        else:

            source_location = geolocator.geocode(
                source + ", Chennai, India"
            )

            if source_location is None:
                return jsonify({
                    "success": False,
                    "message": "Source location not found."
                })

            start_lat = source_location.latitude
            start_lon = source_location.longitude

        # ============================================
        # DESTINATION COORDINATES
        # ============================================

        if destination.lower() == "semmancheri":

            destination_lat = 12.8700
            destination_lon = 80.2267

        else:

            destination_location = geolocator.geocode(
                destination + ", Chennai, India"
            )

            if destination_location is None:
                return jsonify({
                    "success": False,
                    "message": "Destination location not found."
                })

            destination_lat = destination_location.latitude
            destination_lon = destination_location.longitude

        # ============================================
        # PRINT COORDINATES
        # ============================================

        print("===================================")

        print("📍 Source:", source)
        print(
            "Source coordinates:",
            start_lat,
            start_lon
        )

        print("🏁 Destination:", destination)
        print(
            "Destination coordinates:",
            destination_lat,
            destination_lon
        )

        print("===================================")

        # ============================================
        # BUILD ROAD GRAPH
        # ============================================

        north = max(
            start_lat,
            destination_lat
        ) + 0.01

        south = min(
            start_lat,
            destination_lat
        ) - 0.01

        east = max(
            start_lon,
            destination_lon
        ) + 0.01

        west = min(
            start_lon,
            destination_lon
        ) - 0.01

        graph = ox.graph_from_bbox(
            (
                west,
                south,
                east,
                north
            ),
            network_type="drive"
        )

        # ============================================
        # FIND NEAREST NODES
        # ============================================

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

        # ============================================
        # FIND SHORTEST ROUTE
        # ============================================

        route = nx.shortest_path(
            graph,
            start_node,
            destination_node,
            weight="length"
        )

        # ============================================
        # CALCULATE DISTANCE
        # ============================================

        distance_meters = calculate_distance(
            graph,
            route
        )

        distance_km = round(
            distance_meters / 1000,
            2
        )

        # ============================================
        # CALCULATE TRAVEL TIME
        # ============================================

        #travel_time_seconds = calculate_travel_time(
            #graph,
            #oute
        #)
        emergency_speed_kmh = 40

        time_minutes = max(
            1,
            round(
                (distance_km / emergency_speed_kmh) * 60
            )
        )

        # ============================================
        # CONVERT ROUTE TO COORDINATES
        # ============================================

        route_coordinates = route_to_coordinates(
            graph,
            route
        )

        # ============================================
        # SAVE ROUTE DATA
        # ============================================

        route_data = {
            "route": route_coordinates,
            "distance": distance_km,
            "time": time_minutes
        }

        print("✅ Route calculated successfully")
        print("Distance:", distance_km, "km")
        print("Time:", time_minutes, "minutes")
        # =============================================
        # 🗄️ SAVE ROUTE TO DATABASE
        # =============================================

        connection = sqlite3.connect(DATABASE)

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO emergency_incidents
(
    source,
    destination,
    vehicle_type,
    distance,
    travel_time,
    route_type,
    status,
    created_at
)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (
            source,
            destination,
            "Ambulance",
            round(distance_km, 2),
            time_minutes,
            "Shortest Route",
            "Completed"
        ))

        connection.commit()

        connection.close()

        print(
            "🗄️ Route saved to database successfully"
        )
        
        # ============================================
        # RETURN RESPONSE
        # ============================================

        return jsonify({
            "success": True,
            "route": route_coordinates,
            "distance": distance_km,
            "time": time_minutes,
            "original_distance": distance_km,
            "original_time": time_minutes,
            "alternate": False,
            "alternate_distance": None,
            "alternate_time": None,
            "recommended_route": "Original Route"
        })

    # ================================================
    # NO ROAD PATH
    # ================================================

    except nx.NetworkXNoPath:

        return jsonify({
            "success": False,
            "message": "No road path found between start and destination."
        }), 400

    # ================================================
    # OTHER ERRORS
    # ================================================

    except Exception as e:

        print(
            "❌ Find route error:",
            e
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
# =====================================================
# SIMULATE ROAD BLOCK
# =====================================================

@app.route(
    "/simulate-block",
    methods=["POST"]
)
def simulate_block():

    try:

        # =============================================
        # FIND START AND DESTINATION
        # =============================================

        start_node, destination_node = (
            get_start_destination(graph)
        )


        # =============================================
        # ORIGINAL ROUTE
        # =============================================

        original_route = nx.shortest_path(
            graph,
            start_node,
            destination_node,
            weight="length"
        )


        # =============================================
        # ORIGINAL DISTANCE
        # =============================================

        original_distance = calculate_distance(
            graph,
            original_route
        )

        original_distance_km = (
            original_distance / 1000
        )


        # =============================================
        # ORIGINAL TRAVEL TIME
        # =============================================

        original_time_seconds = calculate_travel_time(
            graph,
            original_route
        )

        original_time_minutes = max(
            1,
            round(
                original_time_seconds / 60
            )
        )


        # =============================================
        # FIND ROAD TO BLOCK
        # =============================================

        middle = len(original_route) // 2

        indexes = list(
            range(
                middle,
                len(original_route) - 1
            )
        )

        indexes += list(
            range(
                middle - 1,
                0,
                -1
            )
        )


        # =============================================
        # TRY ROAD BLOCKS
        # =============================================

        for i in indexes:

            node_a = original_route[i]
            node_b = original_route[i + 1]


            # =========================================
            # CREATE COPY OF ROAD NETWORK
            # =========================================

            blocked_graph = graph.copy()


            # =========================================
            # REMOVE A -> B
            # =========================================

            if blocked_graph.has_edge(
                node_a,
                node_b
            ):

                edge_data = (
                    blocked_graph.get_edge_data(
                        node_a,
                        node_b
                    )
                )

                for key in list(
                    edge_data.keys()
                ):

                    blocked_graph.remove_edge(
                        node_a,
                        node_b,
                        key
                    )


            # =========================================
            # REMOVE B -> A
            # =========================================

            if blocked_graph.has_edge(
                node_b,
                node_a
            ):

                edge_data = (
                    blocked_graph.get_edge_data(
                        node_b,
                        node_a
                    )
                )

                for key in list(
                    edge_data.keys()
                ):

                    blocked_graph.remove_edge(
                        node_b,
                        node_a,
                        key
                    )


            # =========================================
            # FIND ALTERNATE ROUTE
            # =========================================

            try:

                alternate_route = nx.shortest_path(
                    blocked_graph,
                    start_node,
                    destination_node,
                    weight="length"
                )


                # =====================================
                # MAKE SURE ROUTE CHANGED
                # =====================================

                if alternate_route == original_route:
                    continue


                # =====================================
                # ALTERNATE DISTANCE
                # =====================================

                alternate_distance = calculate_distance(
                    blocked_graph,
                    alternate_route
                )

                alternate_distance_km = (
                    alternate_distance / 1000
                )


                # =====================================
                # ALTERNATE TRAVEL TIME
                # =====================================

                alternate_time_seconds = (
                    calculate_travel_time(
                        blocked_graph,
                        alternate_route
                    )
                )

                alternate_time_minutes = max(
                    1,
                    round(
                        alternate_time_seconds / 60
                    )
                )


                # =====================================
                # CONVERT ALTERNATE ROUTE
                # TO COORDINATES
                # =====================================

                route_coordinates = (
                    route_to_coordinates(
                        blocked_graph,
                        alternate_route
                    )
                )


                # =====================================
                # BLOCKED ROAD COORDINATES
                # =====================================

                blocked_road = [

                    [
                        graph.nodes[node_a]["y"],
                        graph.nodes[node_a]["x"]
                    ],

                    [
                        graph.nodes[node_b]["y"],
                        graph.nodes[node_b]["x"]
                    ]

                ]


                # =====================================
                # COMPARE ROUTES
                # =====================================

                if (
                    alternate_time_minutes
                    < original_time_minutes
                ):

                    recommended_route = (
                        "Alternate Route"
                    )

                    recommendation_reason = (
                        "Alternate route has "
                        "lower travel time."
                    )

                else:

                    recommended_route = (
                        "Original Route"
                    )

                    recommendation_reason = (
                        "Original route has "
                        "lower travel time."
                    )


                # =====================================
                # PRINT INFORMATION
                # =====================================

                print()
                print("=" * 55)
                print("🚑 SMART EMERGENCY ROUTE COMPARISON")
                print("=" * 55)

                print()
                print("📍 ORIGINAL ROUTE")
                print(
                    "Distance:",
                    round(
                        original_distance_km,
                        2
                    ),
                    "km"
                )
                print(
                    "Travel Time:",
                    original_time_minutes,
                    "minutes"
                )

                print()
                print("🚧 ALTERNATE ROUTE")
                print(
                    "Distance:",
                    round(
                        alternate_distance_km,
                        2
                    ),
                    "km"
                )
                print(
                    "Travel Time:",
                    alternate_time_minutes,
                    "minutes"
                )

                print()
                print("🏆 RECOMMENDED ROUTE:")
                print(
                    recommended_route
                )

                print(
                    "Reason:",
                    recommendation_reason
                )

                print()
                print(
                    "Blocked road:",
                    node_a,
                    "->",
                    node_b
                )

                print("=" * 55)
                print()

                # =============================================
                # 🗄️ SAVE ALTERNATE ROUTE TO DATABASE
                # =============================================

                connection = sqlite3.connect(DATABASE)

                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO emergency_incidents
                    (
                        source,
                        destination,
                        vehicle_type,
                        distance,
                        travel_time,
                        route_type,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    "sathyabama institute",
                    "navalur",
                    "Ambulance",
                    round(alternate_distance_km, 2),
                    alternate_time_minutes,
                    "Alternate Route",
                    "Completed"
                ))

                connection.commit()

                connection.close   ()

                print(
                    "🗄️ Alternate route saved to database successfully"
                )
                
                # =====================================
                # SEND RESPONSE TO FRONTEND
                # =====================================

                return jsonify({

                    "success": True,

                    "route":
                    route_coordinates,

                    "distance":
                    round(
                        alternate_distance_km,
                        2
                    ),

                    "time":
                    alternate_time_minutes,

                    "alternate":
                    True,

                    "blocked_road":
                    blocked_road,

                    "message":
                    "Alternate route calculated successfully.",

                    # ---------------------------------
                    # PHASE 3 DATA
                    # ---------------------------------

                    "original_distance":
                    round(
                        original_distance_km,
                        2
                    ),

                    "original_time":
                    original_time_minutes,

                    "alternate_distance":
                    round(
                        alternate_distance_km,
                        2
                    ),

                    "alternate_time":
                    alternate_time_minutes,

                    "recommended_route":
                    recommended_route,

                    "recommendation_reason":
                    recommendation_reason

                })


            except nx.NetworkXNoPath:

                continue


        # =============================================
        # NO ALTERNATE ROUTE
        # =============================================

        return jsonify({

            "success": False,

            "message":
            "No suitable road block found for an alternate route."

        })


    except Exception as e:

        print()
        print("❌ ERROR:", e)
        print()

        return jsonify({

            "success": False,

            "message":
            "Error while calculating alternate route."

        })



# =====================================================
# 🚨 PHASE 5 - MULTIPLE EMERGENCY VEHICLE ROUTES
# =====================================================

@app.route(
    "/multiple-routes",
    methods=["POST"]
)
def multiple_routes():

    try:

        vehicles = [

            {
                "id": "ambulance",
                "name": "Ambulance 1",
                "icon": "🚑",
                "start_lat": 12.8728,
                "start_lon": 80.2194,
                "destination_lat": 12.8810,
                "destination_lon": 80.2300
            },

            {
                "id": "fire",
                "name": "Fire Vehicle",
                "icon": "🚒",
                "start_lat": 12.8705,
                "start_lon": 80.2205,
                "destination_lat": 12.8765,
                "destination_lon": 80.2260
            },

            {
                "id": "police",
                "name": "Police Vehicle",
                "icon": "🚓",
                "start_lat": 12.8750,
                "start_lon": 80.2155,
                "destination_lat": 12.8830,
                "destination_lon": 80.2185
            }
        ]

        results = []

        # =================================================
        # CALCULATE ROUTE FOR EACH VEHICLE SEPARATELY
        # =================================================

        for vehicle in vehicles:

            print("\n======================================")
            print("🚨 Vehicle:", vehicle["name"])
            print("======================================")

            # ---------------------------------------------
            # CREATE BOUNDING BOX FOR THIS VEHICLE
            # ---------------------------------------------

            north = max(
                vehicle["start_lat"],
                vehicle["destination_lat"]
            ) + 0.01

            south = min(
                vehicle["start_lat"],
                vehicle["destination_lat"]
            ) - 0.01

            east = max(
                vehicle["start_lon"],
                vehicle["destination_lon"]
            ) + 0.01

            west = min(
                vehicle["start_lon"],
                vehicle["destination_lon"]
            ) - 0.01

            # ---------------------------------------------
            # BUILD SEPARATE ROAD GRAPH
            # ---------------------------------------------

            vehicle_graph = ox.graph_from_bbox(
                (
                    west,
                    south,
                    east,
                    north
                ),
                network_type="drive"
            )

            # ---------------------------------------------
            # FIND NEAREST START NODE
            # ---------------------------------------------

            start_node = ox.distance.nearest_nodes(
                vehicle_graph,
                vehicle["start_lon"],
                vehicle["start_lat"]
            )

            # ---------------------------------------------
            # FIND NEAREST DESTINATION NODE
            # ---------------------------------------------

            destination_node = ox.distance.nearest_nodes(
                vehicle_graph,
                vehicle["destination_lon"],
                vehicle["destination_lat"]
            )

            print("Start node:", start_node)
            print("Destination node:", destination_node)

            # ---------------------------------------------
            # FIND SHORTEST ROUTE
            # ---------------------------------------------

            route = nx.shortest_path(
                vehicle_graph,
                start_node,
                destination_node,
                weight="length"
            )

            # ---------------------------------------------
            # DISTANCE
            # ---------------------------------------------

            distance_meters = calculate_distance(
                vehicle_graph,
                route
            )

            distance_km = round(
                distance_meters / 1000,
                2
            )

            # ---------------------------------------------
            # TRAVEL TIME
            # ---------------------------------------------

            #travel_time_seconds = calculate_travel_time(
                #vehicle_graph,
                #route
            #)

            time_minutes = max(
                1,
                round(
                     distance_km / 40 * 60
                )
               
                    
            )
            

            # ---------------------------------------------
            # CONVERT ROUTE TO LAT/LON
            # ---------------------------------------------

            route_coordinates = route_to_coordinates(
                vehicle_graph,
                route
            )

            print(
                "📏 Distance:",
                distance_km,
                "km"
            )

            print(
                "⏱️ Time:",
                time_minutes,
                "minutes"
            )

            # ---------------------------------------------
            # STORE RESULT
            # ---------------------------------------------

            results.append(
                {
                    "id": vehicle["id"],
                    "name": vehicle["name"],
                    "icon": vehicle["icon"],
                    "route": route_coordinates,
                    "distance": distance_km,
                    "time": time_minutes
                }
            )

        # =================================================
        # SEND RESULTS TO FRONTEND
        # =================================================

        return jsonify(
            {
                "success": True,
                "vehicles": results
            }
        )

    # =====================================================
    # NO PATH ERROR
    # =====================================================

    except nx.NetworkXNoPath:

        return jsonify(
            {
                "success": False,
                "message":
                    "No road path found for one of the emergency vehicles."
            }
        ), 400

    # =====================================================
    # OTHER ERROR
    # =====================================================

    except Exception as e:

        print(
            "❌ Multiple vehicle error:",
            e
        )

        return jsonify(
            {
                "success": False,
                "message": str(e)
            }
        ), 500


# =====================================================
# 🧠 PHASE 6 - AI INTELLIGENT ROUTE OPTIMIZATION
# =====================================================

@app.route(
    "/ai-optimize",
    methods=["POST"]
)
def ai_optimize():

    try:

        # =============================================
        # FIND START AND DESTINATION
        # =============================================

        start_node, destination_node = get_start_destination(
            graph
        )


        # =============================================
        # CREATE SIMPLE DIRECTED GRAPH
        # =============================================

        simple_graph = nx.DiGraph()

        for node, data in graph.nodes(data=True):
            simple_graph.add_node(
                node,
                **data
            )


        # =============================================
        # SELECT BEST EDGE BETWEEN NODES
        # =============================================

        for u, v, data in graph.edges(data=True):

            travel_time = data.get(
                "travel_time",
                data.get("length", 1)
            )

            if (
                not simple_graph.has_edge(u, v)
                or travel_time <
                simple_graph[u][v].get(
                    "travel_time",
                    float("inf")
                )
            ):

                simple_graph.add_edge(
                    u,
                    v,
                    **data
                )


        # =============================================
        # GENERATE MULTIPLE POSSIBLE ROUTES
        # =============================================

        route_generator = nx.shortest_simple_paths(
            simple_graph,
            start_node,
            destination_node,
            weight="travel_time"
        )


        candidate_routes = []

        for route in route_generator:

            candidate_routes.append(
                route
            )

            if len(candidate_routes) >= 5:
                break


        # =============================================
        # CHECK ROUTES
        # =============================================

        if not candidate_routes:

            return jsonify({
                "success": False,
                "message": "No possible routes found."
            }), 400


        # =============================================
        # CALCULATE ROUTE INFORMATION
        # =============================================

        route_data = []


        for route in candidate_routes:

            distance_meters = calculate_distance(
                simple_graph,
                route
            )

            travel_time_seconds = calculate_travel_time(
                simple_graph,
                route
            )


            # =========================================
            # ROAD QUALITY SCORE
            # =========================================

            road_penalty = 0


            for i in range(
                len(route) - 1
            ):

                node_a = route[i]
                node_b = route[i + 1]


                edge_data = simple_graph.get_edge_data(
                    node_a,
                    node_b
                )


                if edge_data is None:
                    continue


                highway = edge_data.get(
                    "highway",
                    "unclassified"
                )


                if isinstance(
                    highway,
                    list
                ):
                    highway = highway[0]


                if highway in [
                    "motorway",
                    "trunk"
                ]:

                    road_penalty += 0


                elif highway in [
                    "primary",
                    "secondary"
                ]:

                    road_penalty += 1


                elif highway == "tertiary":

                    road_penalty += 2


                elif highway in [
                    "residential",
                    "living_street"
                ]:

                    road_penalty += 3


                else:

                    road_penalty += 4


            route_data.append({

                "route": route,

                "distance":
                    distance_meters,

                "time":
                    travel_time_seconds,

                "road_penalty":
                    road_penalty

            })


        # =============================================
        # NORMALIZATION
        # =============================================

        max_distance = max(
            r["distance"]
            for r in route_data
        )

        max_time = max(
            r["time"]
            for r in route_data
        )

        max_penalty = max(
            r["road_penalty"]
            for r in route_data
        )


        if max_distance == 0:
            max_distance = 1

        if max_time == 0:
            max_time = 1

        if max_penalty == 0:
            max_penalty = 1


        # =============================================
        # 🧠 AI ROUTE SCORING
        # =============================================

        for r in route_data:

            distance_score = (
                r["distance"] /
                max_distance
            )

            time_score = (
                r["time"] /
                max_time
            )

            road_score = (
                r["road_penalty"] /
                max_penalty
            )


            # Lower score = better route

            r["ai_score"] = (

                distance_score * 0.30

                +

                time_score * 0.50

                +

                road_score * 0.20

            )


        # =============================================
        # 🏆 SELECT BEST ROUTE
        # =============================================

        best_route = min(
            route_data,
            key=lambda x: x["ai_score"]
        )


        # =============================================
        # CONVERT ROUTE TO LAT/LON
        # =============================================

        route_coordinates = route_to_coordinates(
            simple_graph,
            best_route["route"]
        )


        # =============================================
        # ROUTE COMPARISON
        # =============================================

        comparisons = []


        for index, r in enumerate(
            route_data
        ):

            comparisons.append({

                "route_number":
                    index + 1,

                "distance":
                    round(
                        r["distance"] / 1000,
                        2
                    ),

                "time":
                    max(
                        1,
                        round(
                            r["time"] / 60
                        )
                    ),

                "ai_score":
                    round(
                        r["ai_score"],
                        4
                    ),

                "road_penalty":
                    r["road_penalty"],

                "selected":
                    r is best_route

            })


        # =============================================
        # RETURN AI RESULT
        # =============================================

        return jsonify({

            "success": True,

            "route":
                route_coordinates,

            "distance":
                round(
                    best_route["distance"] / 1000,
                    2
                ),

            "time":
                max(
                    1,
                    round(
                        best_route["time"] / 60
                    )
                ),

            "ai_score":
                round(
                    best_route["ai_score"],
                    4
                ),

            "comparisons":
                comparisons,

            "message":
                "🧠 AI selected the best emergency route."

        })


    # =============================================
    # NO ROUTE
    # =============================================

    except nx.NetworkXNoPath:

        return jsonify({

            "success": False,

            "message":
                "No route available between start and destination."

        }), 400


    # =============================================
    # OTHER ERROR
    # =============================================

    except Exception as e:

        print()
        print(
            "❌ AI optimization error:",
            e
        )
        print()

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500
    # =====================================================
# 📊 PHASE 7 - DASHBOARD API
# =====================================================

@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    # ---------------------------------------------
    # TOTAL ROUTES
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM emergency_incidents
    """)

    total_routes = cursor.fetchone()[0]

    # ---------------------------------------------
    # SHORTEST ROUTES
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM emergency_incidents
        WHERE route_type = 'Shortest Route'
    """)

    shortest_routes = cursor.fetchone()[0]

    # ---------------------------------------------
    # ALTERNATE ROUTES
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM emergency_incidents
        WHERE route_type = 'Alternate Route'
    """)

    alternate_routes = cursor.fetchone()[0]

    # ---------------------------------------------
    # COMPLETED ROUTES
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM emergency_incidents
        WHERE status = 'Completed'
    """)

    completed_routes = cursor.fetchone()[0]

    # ---------------------------------------------
    # RECENT ROUTES
    # ---------------------------------------------

    cursor.execute("""
        SELECT
            id,
            source,
            destination,
            vehicle_type,
            distance,
            travel_time,
            route_type,
            status,
            created_at
        FROM emergency_incidents
        ORDER BY id DESC
        LIMIT 10
    """)

    recent_routes = cursor.fetchall()

    connection.close()

    routes = []

    for row in recent_routes:

        routes.append({
            "id": row[0],
            "source": row[1],
            "destination": row[2],
            "vehicle_type": row[3],
            "distance": row[4],
            "travel_time": row[5],
            "route_type": row[6],
            "status": row[7],
            "created_at": row[8]
        })

    return jsonify({

        "success": True,

        "total_routes": total_routes,

        "shortest_routes": shortest_routes,

        "alternate_routes": alternate_routes,

        "completed_routes": completed_routes,

        "recent_routes": routes
    })

# =====================================================
# RUN FLASK
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )