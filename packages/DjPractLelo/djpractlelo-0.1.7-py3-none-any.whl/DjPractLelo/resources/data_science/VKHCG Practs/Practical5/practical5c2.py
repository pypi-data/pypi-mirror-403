import pandas as pd, networkx as nx, matplotlib.pyplot as plt

input_file = "C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/02-Python/Retrieve_Router_Location.csv"

# Load all data
df = pd.read_csv(input_file, encoding="latin-1", low_memory=False)
print('Loaded Columns:', df.columns.values)
print('Rows:', df.shape[0])
print('################################')
print(df)
print('################################')

# Create graph and positions
G = nx.Graph()
pos = {}
for i in range(df.shape[0]):
    lat = round(df['Latitude'][i], 2)
    lon = round(df['Longitude'][i], 2)
    gps_label = f"{abs(lat)}{'S' if lat<0 else 'N'}-{abs(lon)}{'W' if lon<0 else 'E'}"
    G.add_node(gps_label)
    pos[gps_label] = (lon, lat)

# Add visual links (edges)
for n1 in G.nodes():
    for n2 in G.nodes():
        if n1 != n2:
            G.add_edge(n1, n2)

# Print links
for n1, n2 in G.edges():
    print('Link :', n1, ' to ', n2)

print('################################')
print("Nodes of graph:", G.number_of_nodes())
print("Edges of graph:", G.number_of_edges())
print('################################')

# Draw graph
plt.figure(figsize=(12,10))
nx.draw(G, pos=pos, with_labels=True, node_size=400, node_color='red', edge_color='blue', font_size=8)
plt.title("Network Graph of GPS Locations (All Rows)")
plt.show()
