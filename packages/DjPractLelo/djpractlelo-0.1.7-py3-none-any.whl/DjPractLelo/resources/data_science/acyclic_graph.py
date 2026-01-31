import networkx as nx

G = nx.DiGraph()

G.add_edge("Start", "Process1")
G.add_edge("Process1", "Process2")
G.add_edge("Process2", "Process3")
G.add_edge("Process3", "End")
G.add_edge("Start", "ProcessA")
G.add_edge("ProcessA", "ProcessB")
G.add_edge("ProcessB", "End")

print("Edges:", G.edges())

if nx.is_directed_acyclic_graph(G):
    print("Graph is Acyclic")
else:
    print("Graph has a Cycle")
