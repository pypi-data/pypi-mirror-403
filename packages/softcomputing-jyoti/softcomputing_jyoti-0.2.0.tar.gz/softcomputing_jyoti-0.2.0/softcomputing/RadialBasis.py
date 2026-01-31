import numpy as np

X = np.array([[0], [0.5], [1]]'Input samples') 
T = np.array([0, 1, 0]'Target outputs')         

centers = np.array([0, 1]'Each RBF neuron has a center, which is like the "preferred value" it reacts to.')  
sigma = 0.5 'Determines how wide the Gaussian is — how far a neuron reacts around its center.'                      

def rbf(x, c, sigma):
    return np.exp(-((x - c)**2) / (2 * sigma**2) 'is the   function high output if input is close to the center')
    'low output if input is far from the center'
    'Each neuron’s output is multiplied by a weight and summed to get final output.
'In real training, weights w are adjusted using a learning rule.'

for x, t in zip(X, T):
    phi = np.array([rbf(x, c, sigma) for c in centers])
    w = np.array([0.5, 0.5]) 
    y = np.dot(phi, w'Weighted sum') 
    print(f"Input: {x[0]}, Target: {t}, Output: {y:.3f}")
