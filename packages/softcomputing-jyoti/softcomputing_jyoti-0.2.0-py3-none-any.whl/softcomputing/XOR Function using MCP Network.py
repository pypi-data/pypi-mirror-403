inputs = [(0,0), (0,1), (1,0), (1,1)]

def mp_and_not(x1, x2):
    return 1 if x1 - x2 >= 1 else 0

def mp_not_and(x1, x2):
    return 1 if x2 - x1 >= 1 else 0

Y = []
for x1, x2 in inputs:
    h1 = mp_and_not(x1, x2)
    h2 = mp_not_and(x1, x2)
    y = 1 if h1 + h2 >= 1 else 0
    Y.append(y)

for inp, out in zip(inputs, Y):
    print(f"Input: {inp} -> XOR Output: {out}")
