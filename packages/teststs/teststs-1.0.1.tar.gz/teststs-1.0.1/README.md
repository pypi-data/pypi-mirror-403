# Teststs
A Simple, Tiny Test Library for Python

## Using

```py
from teststs import teststs

def add_five(inp):
    return int(inp) + 5

tests = [
    ("5", 10),
    ("10", 15),
]

teststs(tests, add_five, detail=True)
teststs(tests, add_five, detail=False) # Default

```
