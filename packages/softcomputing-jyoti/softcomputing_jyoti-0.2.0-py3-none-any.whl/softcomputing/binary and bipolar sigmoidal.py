import numpy as np

binary = lambda x: 1 / (1 + np.exp(-x))
bipolar = lambda x: 2 / (1 + np.exp(-x)) - 1

x = np.array([1, 0, -1])
w = np.array([[0.4, -0.3],
              [0.3,  0.8],
              [0.5, -0.6]])
b = np.array([0.1, -0.1])

net = np.dot(x, w) + b

print("Binary Sigmoid Output:", binary(net))
print("Bipolar Sigmoid Output:", bipolar(net))
