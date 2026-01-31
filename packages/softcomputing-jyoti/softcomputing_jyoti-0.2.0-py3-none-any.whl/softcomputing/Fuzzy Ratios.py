from fuzzywuzzy import fuzz, process

s1 = "I love fuzzysforfuzzys"
s2 = "I am loving fuzzysforfuzzys"

print("Fuzzy Ratio:", fuzz.ratio(s1, s2))
print("Partial Ratio:", fuzz.partial_ratio(s1, s2))

query = "fuzzys for fuzzys"
choices = ["fuzzy for fuzzy", "fuzzy fuzzy", "g. for fuzzys"]
print("Best Match:", process.extractOne(query, choices))
