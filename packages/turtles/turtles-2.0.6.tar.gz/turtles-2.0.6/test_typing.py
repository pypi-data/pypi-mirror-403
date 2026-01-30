"""Test file to verify type inference with the stub file."""
from turtles import Rule, optional, sequence, repeat, either, char, at_least
from typing import TYPE_CHECKING, cast

# Test grammar definition
class A(Rule):
    value: repeat[char[r"a-z"], at_least[1]]  # noqa

class B(Rule):
    word: optional[A]

class C(Rule):
    items: sequence[B, B, A, B]

class D(Rule):
    value: either[A, B]

if not TYPE_CHECKING:
    def reveal_type(*args, **kwargs) -> None:...

apple = A("hello")
a = apple.value
banana = B("hello")
b = banana.word
if isinstance(b, A):
    b
else:
    b
cherry = C("hello hello")
c = cherry.items
c0 = cherry.items[2]
date = D("hello")
d = date.value
if isinstance(d, A):
    d
else:
    d
    d = cast(B, d)
    if d.word is not None:
        d.word
    else:
        d.word

# # Test that type inference works correctly
# def check_types() -> None:
#     # After parsing, what types should we see?
    
#     opt_result = OptionalWord("hello")
#     # opt_result.word should be Word | None
#     if opt_result.word is not None:
#         # After narrowing, should be Word
#         reveal_type(opt_result.word)  # pyright: Word
#         print(opt_result.word.value)
    
#     pair_result = Pair("hello world")  
#     # pair_result.items should be tuple[Word, Word]
#     reveal_type(pair_result.items)  # pyright: tuple[Word, Word]
#     first, second = pair_result.items
    
#     word_result = Word("hello")
#     # word_result.value should be list[char] or str
#     reveal_type(word_result.value)  # pyright: list[char]
