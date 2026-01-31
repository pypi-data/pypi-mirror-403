import numpy as np

patterns = np.array([[1, -1, 1], [-1, 1, -1]]'Stored patterns (1 or -1) 1 = neuron on -1 of fneuron ')

W = np.zeros((3,3))
for p in patterns:
    W += np.outer(p, p)
np.fill_diagonal(W, 0'No self-connection') 

x = np.array([1, -1, -1])

for _ in range(5):
    for i in range(len(x)):
        x[i] = 1 if np.dot(W[i], x) >= 0 else -1
    print("State:", x)
