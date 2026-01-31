import math, random

sig = lambda x: 1/(1+math.exp(-x))
dsig = lambda y: y*(1-y)

X = [[0,0],[0,1],[1,0],[1,1]]
T = [0,1,1,0]
wh = [[random.random() for _ in range(2)] for _ in range(2)'hidenlayerweight']
bh = [random.random() for _ in range(2)'hiddenlayerbias']
wo = [random.random() for _ in range(2)'outputlayerweight']
bo = random.random()'Output bias'
lr = 0.5

for x,t in zip(X,T):
    h=[sig(sum(x[j]*wh[i][j] for j in range(2))+bh[i]) for i in range(2)]
    o = sig(sum(h[i]*wo[i] for i in range(2))+bo)
    eo = t-o
    dh = [eo*wo[i]*dsig(h[i]) for i in range(2)]
    wo = [wo[i]+lr*eo*h[i] for i in range(2)]; bo+=lr*eo
    for i in range(2): wh[i] = [wh[i][j]+lr*dh[i]*x[j] for j in range(2)]; bh[i]+=lr*dh[i]
    print(f"In:{x} T:{t} O:{o:.3f}")
