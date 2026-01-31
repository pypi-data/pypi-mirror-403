import pandas as pd

# Read the file (replace with your actual path)
df = pd.read_csv('C:/msc_dataset/Practical_3c/IP_DATA_CORE.csv', usecols=['Country', 'Place Name', 'Latitude'], encoding='latin-1')
df.rename(columns={'Place Name': 'Place_Name'}, inplace=True)

# Filter for London
data = df[df['Place_Name'] == 'London']

# Calculate mean and std
mean = data['Latitude'].mean()
std = data['Latitude'].std()

# Calculate bounds
lower, upper = mean - std, mean + std

# Filter data
outliers_high = data[data['Latitude'] > upper]
outliers_low = data[data['Latitude'] < lower]
not_outliers = data[(data['Latitude'] >= lower) & (data['Latitude'] <= upper)]

# Print results
print('Higher than', upper, '\n', outliers_high)
print('Lower than', lower, '\n', outliers_low)
print('Not Outliers\n', not_outliers)
