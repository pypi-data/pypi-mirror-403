# Simple Hebbian Learning for a single neuron

w = float(input("Enter initial weight:0.5 "))       
lr = float(input("Enter learning rate: 0.1"))      
x = float(input("Enter input x:1 "))             
y = float(input("Enter neuron output y:1 "))      
n = int(input("Enter number of iterations: 5"))   

for i in range(1, n + 1):

    delta_w = lr * x * y
    w += delta_w
    print(f"Iteration {i}: delta = {delta_w}, Updated weight = {w}")
