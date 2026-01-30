from turtles import Rule, char, repeat, at_least, separator

# define rules for our grammar
class Int(Rule, int):
    value: repeat[char["0-9"], at_least[1]]

class Float(Rule, float):
    whole: Int
    "."
    frac: Int

Number = Float | Int

class KV(Rule):
    key: repeat[char["a-zA-Z_"], at_least[1]]
    "="
    value: Number

class Row(Rule):
    items: repeat[KV, separator[" "], at_least[1]]


# parse some input with the grammar
src = "temp=21.5 humidity=45 retries=0"
row = Row(src)

# Work with hydrated objects
assert row.items[0].key == "temp"
assert row.items[0].value == 21.5

# Convert the whole parse result to plain Python containers
data = row.as_dict()
assert data == {
    "items": [
        {"key": "temp", "value": 21.5},
        {"key": "humidity", "value": 45},
        {"key": "retries", "value": 0},
    ]
}

# # Helpful while iterating on a grammar
print(repr(row))
# Row
# └── items: [3 items]
#     ├── [0]: KV
#     │   ├── key: temp
#     │   └── value: Float
#     │       ├── whole: Int
#     │       │   └── value: 21
#     │       └── frac: Int
#     │           └── value: 5
#     ├── [1]: KV
#     │   ├── key: humidity
#     │   └── value: Int
#     │       └── value: 45
#     └── [2]: KV
#         ├── key: retries
#         └── value: Int
#             └── value: 0