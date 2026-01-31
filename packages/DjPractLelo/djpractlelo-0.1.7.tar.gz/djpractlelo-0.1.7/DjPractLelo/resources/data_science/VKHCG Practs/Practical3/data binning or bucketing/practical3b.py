import numpy as np
import matplotlib.pyplot as plt

# Seed for reproducibility
np.random.seed(0)

# Generate sample data
mean = 90
sigma = 25
data = mean + sigma * np.random.randn(50)

bins = 25

# Creation of histogram
counts, bins, patches = plt.hist(data, bins=bins, density=False, alpha=0.7, color='blue')

plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title(f'Histogram: {len(data)} entries binned into {bins} buckets')
plt.show()
