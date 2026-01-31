import numpy as np
from minisom import MiniSom
import matplotlib.pyplot as plt

colors = np.array([[0,0,0],[0,0,1],[0,1,0],[1,0,0],[1,1,0],[0,1,1],[1,0,1],[1,1,1]])
names  = ['black','blue','green','red','yellow','cyan','magenta','white']

som = MiniSom(10,10,3,'creates a SOM grid with 10×10 neurons and 3 inputs per neuron (for RGB)'
sigma=1.0'determines how much neighboring neurons are updated when one neuron wins', learning_rate=0.5'speed of learning')
som.train(colors, 50'trains SOM using 50 iterations with the RGB inputs.')

plt.imshow(som.distance_map().T, cmap='bone')
for i,c in enumerate(colors):
    x,y = som.winner(c)
    plt.text(y,x,names[i],ha='center',va='center',bbox=dict(facecolor='white',alpha=0.5,lw=0))
plt.show()
