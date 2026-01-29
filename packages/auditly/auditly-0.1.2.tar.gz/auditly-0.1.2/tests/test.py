from importlib.metadata import distributions

names = []
for d in distributions():
    names.append(d.metadata.get("Name"))

print(len(names))                      # 45
print(len([n for n in names if n]))    # 43
print([n for n in names if not n])     # <-- these are the missing 2
