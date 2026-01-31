import numpy as np

# 1. Store patterns (-1 and 1 only)
p1 = np.array([1, -1, 1, -1])
p2 = np.array([-1, 1, -1, 1])
patterns = [p1, p2]

# 2. Create weight matrix
W = np.zeros((4, 4))
for p in patterns:
    W += np.outer(p, p)
np.fill_diagonal(W, 0)

# 3. Recall function
def recall(x):
    for _ in range(5):           # update few times
        x = np.sign(W @ x)
    return x

# 4. Noisy input
test = np.array([1, -1, -1, -1])

# 5. Output
print("Noisy Input :", test)
print("Recalled    :", recall(test))
