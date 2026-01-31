import pandas as pd
from sklearn.cluster import KMeans

data = {
    "X": [10, 12, 30, 32, 15, 35, 11, 29, 31],
    "Y": [20, 22, 40, 42, 25, 45, 19, 39, 41]
}

df = pd.DataFrame(data)

kmeans = KMeans(n_clusters=2, n_init=10)
df["Cluster"] = kmeans.fit_predict(df)

print(df)
