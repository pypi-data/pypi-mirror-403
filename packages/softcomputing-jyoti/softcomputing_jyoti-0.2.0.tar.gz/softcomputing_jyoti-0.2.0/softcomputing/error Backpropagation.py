import math

sig = lambda x: 1/(1+math.exp(-x))
dsig = lambda y: y*(1-y)

x = float(input("x: 1"))
w = float(input("w: 0.5"))
b = float(input("b:1 "))
t = float(input("target: 0.8"))
lr = float(input("learning rate: 0.1"))
n = int(input("iterations: 5"))

for i in range(n):
    y = sig(w*x + b'forwardpass')        
    e = t - y'error'                  
    delta = e * dsig(y)'backpropogation'        
    w += lr * delta * x'updateweight'       
    b += lr * delta  'update biase'         
    print(f"Iter{i+1}: y={y:.3f}, w={w:.3f}, b={b:.3f}")
