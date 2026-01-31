n = int(input("Enter number of elements: as 3"))

print("Enter input values: 1 2 3 ")
x = [float(input()) for _ in range(n)]

print("Enter weight values: 0.2 0.3 0.5")
w = [float(input()) for _ in range(n)]

print("Net input (Yin) =", round(sum(a*b for a, b in zip(x, w)), 3))