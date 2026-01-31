import numpy as np

patterns = np.array([[1, -1, 1, -1],
                     [-1, 1, -1, 1]])
n = patterns.shape[1]
W = np.zeros((n, n))
for p in patterns:
    W += np.outer(p, p)
np.fill_diagonal(W, 0) 

test = np.array([1, -1, -1, -1])
state = test.copy()

for _ in range(5): 
    for i in range(n):
        state[i] = 1 if np.dot(W[i], state) >= 0 else -1

print("Noisy input:", test)
print("Recalled pattern:", state)
