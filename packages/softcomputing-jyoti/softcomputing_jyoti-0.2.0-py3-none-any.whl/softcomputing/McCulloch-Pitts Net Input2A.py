def MP_AND(x1, x2):
    threshold = 2 
    return 1 if (x1 + x2) >= threshold else 0

def MP_NOT(x):
    threshold = 0 
    return 1 if (-1 * x) >= threshold else 0

inputs = [0, 1]

print("AND Gate:")
for x1 in inputs:
    for x2 in inputs:
        print(f"AND({x1},{x2}) = {MP_AND(x1,x2)}")

print("\nNOT Gate:")
for x in inputs:
    print(f"NOT({x}) = {MP_NOT(x)}")
