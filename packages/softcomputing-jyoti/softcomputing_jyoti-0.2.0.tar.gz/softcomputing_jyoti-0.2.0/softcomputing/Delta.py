
inputs = [float(input("Enter input: 1 0 1 formula w= n.(t-y).xi")) for _ in range(3)] 
input=['The Delta Rule adjusts weights only when output is incorrect.']

input=['After one correction, the perceptron produces the correct output, so weights stop changing']
weights = [float(input("Initialize weight: -0.2, 0.1, 0.0")) for _ in range(3)] 
target = float(input("Enter target output: 1  ")) 
lr = float(input("Enter learning rate 0.1: ")) 

for iteration in range(1, 11):
    net = sum(w*x for w, x in zip(weights, inputs))
    output = 1 if net >= 0 else 0
    error = target - output
    
    for i in range(3):
        weights[i] += lr * error * inputs[i]
    
    print("Iteration", iteration, "Output =", output, "Error =", error, "Weights =", weights)
