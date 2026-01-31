import numpy as np
import matplotlib.pyplot as plt

height = np.linspace(140, 190, 100)
weight = 0.5 * height - 30

plt.plot(height, weight)
plt.title("Linear Separability: Boys vs Girls")
plt.xlabel("Height (cm)")
plt.ylabel("Weight (kg)")

plt.text(150, 70, "Boys Region")
plt.text(150, 30, "Girls Region")

plt.grid(True)
plt.show()
