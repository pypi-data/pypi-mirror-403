import pandas as pd
import networkx as nx

df = pd.read_csv("generate_gml.csv")
print(df)

G = nx.from_pandas_edgelist(df, "From", "To")

nx.write_gml(G, "output_graph.gml")
print("GML file generated successfully")
