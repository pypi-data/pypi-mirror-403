# from turtles import Rule, char, repeat, at_least, either, separator

# class Int(Rule, int):
#     value: repeat[char["0-9"], at_least[1]]

# class Number(Rule, float):
#     whole: repeat[char["0-9"], at_least[1]]
#     '.'
#     frac: repeat[char["0-9"], at_least[1]]

# class Bool(Rule):
#     value: either[r"true", r"false"] # noqa
#     def __convert__(self):
#         if self.value == "true":
#             return True
#         elif self.value == "false":
#             return False
        
#         # unreachable
#         raise ValueError(f"Invalid boolean value. expected 'true' or 'false', got '{self.value}'")

# class ID(Rule, str):
#     first: char["a-zA-Z"] # noqa
#     rest: repeat[char["a-zA-Z0-9"]]  # noqa

# class Digits(Rule):
#     value: repeat[Int, separator[","], at_least[1]]

# # result = Number("1.23")
# result = Bool("false")
# # result = ID("applebanana")
# # result = Int("42")
# # result = Digits("1,2,3,4")
# # result = ID("applebanana1234242")
# # print(result)

from turtles.examples.csv import CSV, Field, Record
from pathlib import Path
import json

here = Path(__file__).parent.resolve()

# Test CSV parsing
csv_src = (here/'example.csv').read_text()
csv = CSV(csv_src)

print('Parse tree (first 2 records):')
for i, record in enumerate(csv.records[:2]):
    print(f'Record {i}: {[str(f) for f in record.fields]}')
print()

print('as_dict (first 2 records):')
print(json.dumps({'records': [r.as_dict() for r in csv.records[:2]]}, indent=2))
