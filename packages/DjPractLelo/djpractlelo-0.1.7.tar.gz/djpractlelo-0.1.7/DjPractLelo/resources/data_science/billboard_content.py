import pandas as pd

data = {
    "Location": ["City", "Highway", "Mall", "Station", "Airport", "Park", "Market"],
    "Visitors": [5000, 9000, 3000, 7000, 10000, 4000, 8500],
    "Ad": ["Food", "Cars", "Clothing", "Mobile", "Travel", "Soft Drinks", "Electronics"]
}

df = pd.DataFrame(data)
print(df)

# Select high traffic locations
selected = df[df["Visitors"] > 6000]

print("\nSelected Billboard Content")
print(selected)
