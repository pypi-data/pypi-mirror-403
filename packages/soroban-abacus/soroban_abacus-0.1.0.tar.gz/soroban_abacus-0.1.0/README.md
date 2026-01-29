# Soroban Abacus

> A simple Soroban abacus supporting positive integers.

## Installation

```bash
uv venv --pytnon=3.14
uv pip install soroban-abacus
```

## Usage

```python
from soroban import Soroban

abacus = Soroban(ncolumns=5)
print(abacus)

0: ●○ | ○○○○
1: ●○ | ○○○○
2: ●○ | ○○○○
3: ●○ | ○○○○
4: ●○ | ○○○○

abacus.from_decimal(17)
print(abacus)

0: ○● | ●●○○
1: ●○ | ●○○○
2: ●○ | ○○○○
3: ●○ | ○○○○
4: ●○ | ○○○○

abacus.to_svg("soroban1.svg")
```

![](./images/soroban1.svg)


```python
from soroban import Soroban

s = Soroban(12)
s.from_decimal(1234567890)
s.to_svg("soroban2.svg")
```

![](./images/soroban2.svg)