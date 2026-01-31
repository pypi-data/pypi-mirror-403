import networkx as nx

G = nx.Graph()

G.add_weighted_edges_from([
    ("India", "Dubai", 4),
    ("Dubai", "USA", 6),
    ("India", "UK", 8),
    ("UK", "USA", 3),
    ("Dubai", "UK", 2),
    ("India", "Germany", 7),
    ("Germany", "USA", 5),
    ("UK", "Canada", 10),
    ("Canada", "USA", 4)
])

route = nx.shortest_path(G, "India", "USA", weight="weight")
print("Best Shipping Route:", route)
