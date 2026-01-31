import numpy as np

X = np.array([[1,1,0,0],
              [1,0,0,0],
              [0,0,1,1],
              [0,0,1,0]])

rho = 0.6
clusters = []

for x in X:
    for i, w in enumerate(clusters):
        if np.sum(x & w) / np.sum(x) >= rho:
            clusters[i] = x & w
            break
    else:  
        clusters.append(x.copy())

print("Clusters formed:", len(clusters))
for i, c in enumerate(clusters):
    print("Cluster", i+1, ":", c)
