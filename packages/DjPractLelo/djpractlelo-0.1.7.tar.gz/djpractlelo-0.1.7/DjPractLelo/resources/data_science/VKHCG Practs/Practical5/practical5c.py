import pandas as pd, networkx as nx, matplotlib.pyplot as plt, os

# File paths
input_file = "C:/VKHCG/01-Vermeulen/01-Retrieve/01-EDS/02-Python/Retrieve_Router_Location.csv"
output_dir = "C:/VKHCG/01-Vermeulen/02-Assess/01-EDS/02-Python"
os.makedirs(output_dir, exist_ok=True)

# Load data
df = pd.read_csv(input_file, encoding="latin-1", low_memory=False)

# Create DAGs for Country and Place-Country
for col, color, fname in [(df['Country'], 'green', "Assess-DAG-Company-Country.png"),
                          (df['Place_Name'] + '-' + df['Country'], 'blue', "Assess-DAG-Company-Country-Place.png")]:
    G = nx.DiGraph()
    G.add_nodes_from(col)
    G.add_edges_from((a,b) for a in col for b in col if a!=b)
    
    # Print links, nodes, edges (only for Country-level)
    if fname == "Assess-DAG-Company-Country.png":
        [print(f"Link : {a} to {b}") for a,b in G.edges()]
        print("################################\n################################")
        print("Nodes of graph:", list(G.nodes()))
        print("Edges of graph:", list(G.edges()))
        print("################################")
    
    # Draw and save DAG
    nx.draw(G, pos=nx.spring_layout(G), node_color='red', edge_color=color,
            with_labels=True, node_size=3000, font_size=10)
    plt.savefig(os.path.join(output_dir, fname))
    plt.show()


