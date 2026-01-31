import matplotlib.pyplot as plt

X = [[0,0],[0,1],[1,0],[1,1]'input for and  gate ']
T = [0,0,0,1'and gate target op'] 
colors = ['red' if t==0 else 'green' for t in T]
for x,c in zip(X,colors):
    plt.scatter(x[0], x[1], color=c, s=100)
import numpy as np
x_vals = np.linspace(-0.5, 1.5, 100)
y_vals = -0.5*x_vals + 0.5 
plt.plot(x_vals, y_vals, 'b--')
plt.xlim(-0.5,1.5); plt.ylim(-0.5,1.5)
plt.xlabel("X1"); plt.ylabel("X2")
plt.title("Linear separability")
plt.show()
