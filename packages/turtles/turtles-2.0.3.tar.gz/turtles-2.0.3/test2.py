# from turtles import Rule, char, repeat, at_least, separator, ParseError


# class Int(Rule):
#     value: repeat[char["0-9"], at_least[1]]


# class Float(Rule):
#     whole: Int
#     "."
#     frac: Int


# Number = Float | Int


# class KV(Rule):
#     key: repeat[char["a-zA-Z_"], at_least[1]]  # noqa
#     "="
#     value: Number


# class Row(Rule):
#     items: repeat[KV, separator[" "], at_least[1]]  # noqa


# row = Row("temp=21.5 humidity=45 retries=0")

# # Work with hydrated objects
# assert row.items[0].key == "temp"
# assert row.items[0].value.as_dict() == {"whole": {"value": "21"}, "frac": {"value": "5"}}

# # Convert the whole parse result to plain Python containers
# data = row.as_dict()
# assert data == {
#     "items": [
#         {"key": "temp", "value": {"whole": {"value": "21"}, "frac": {"value": "5"}}},
#         {"key": "humidity", "value": {"value": "45"}},
#         {"key": "retries", "value": {"value": "0"}},
#     ]
# }

# # Helpful while iterating on a grammar
# print(repr(row))



# try:
#     Row("not_a_kv_pair")
# except ParseError as e:
#     print(e)





from turtles.examples.csv import CSV
from pathlib import Path
here = Path(__file__).parent.resolve()
csv_src = (here/'example.csv').read_text()
csv = CSV(csv_src)
print(repr(csv))
