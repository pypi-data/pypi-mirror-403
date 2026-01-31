import numpy as np

class City:
    def __init__(self, x, y): self.x, self.y = x, y
    def distance_to(self, other): return np.hypot(self.x - other.x, self.y - other.y)
    def __repr__(self): return f"City({self.x},{self.y})"

class Fitness:
    def __init__(self, route): self.route = route
    def distance(self):
        return sum(self.route[i].distance_to(self.route[(i+1)%len(self.route)]) 
                   for i in range(len(self.route)))
    def score(self): return 1 / self.distance()

if __name__ == "__main__":
    route = [City(0,0), City(3,4), City(6,0)]
    fit = Fitness(route)
    print("Route:", route)
    print("Total Distance:", fit.distance())
    print("Fitness Score:", fit.score())
