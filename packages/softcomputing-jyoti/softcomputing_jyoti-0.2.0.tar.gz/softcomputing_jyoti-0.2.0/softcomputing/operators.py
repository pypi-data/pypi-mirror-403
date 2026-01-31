
x = 5
y = 5
z = [5]
print("x is y:", x is y 'identity operators')
print("x is not y:", x is not y)
print("x is z:", x is z)
print("x is not z:", x is not z)

list1 = [1, 2, 3, 4, 5 ' membership operators']
list2 = [6, 7, 8, 9]

if set(list1) & set(list2):
    print("Lists are overlapping")
else:
    print("Lists are NOT overlapping")
