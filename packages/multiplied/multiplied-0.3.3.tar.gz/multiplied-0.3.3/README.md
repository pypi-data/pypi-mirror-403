# multiplied

A powerful tool to build, test, and analyse multiplier designs.

## Why?

Generating and analysing multiplier designs by hand is labour intensive, even
for small datasets, for entire [truth tables](https://en.wikipedia.org/wiki/Truth_table)
, this is close to impossible.

multiplied is built to streamline:

- Custom partial product reduction via [templates](https://github.com/EphraimCompEng/multiplied/blob/master/docs/structures/templates.md)
- Generating complete truth tables
- Analysis, plotting, and managing datasets
- Fine-grain access to bits, words or stages

## Setup

```sh
pip install multiplied
```

```Python
import multiplied as mp
```

## Pattern Based Algorithm

Multiplied assists in template generation to create reusable algorithm objects:

- Patterns are used to build simple templates
- Automatic grouping based on empty rows
- Pseudo outputs help visualise where bits from a given arithmetic unit will land.

```python
m = mp.Matrix(8)
p = mp.Pattern(['a','a','b','b','c','c','d','d'])
alg = mp.Algorithm(m)
alg.push(p)
print(alg)
```

```text
0:{

template:{

________AaAaAaAa
_______aAaAaAaA_
______BbBbBbBb__
_____bBbBbBbB___
____CcCcCcCc____
___cCcCcCcC_____
__DdDdDdDd______
_dDdDdDdD_______

______AaAaAaAaAa
________________
____BbBbBbBbBb__
________________
__CcCcCcCcCc____
________________
DdDdDdDdDd______
________________
}

pseudo:{

______AaAaAaAaAa
____BbBbBbBbBb__
__CcCcCcCcCc____
DdDdDdDdDd______
________________
________________
________________
________________
}

map:{

00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FE FE FE FE FE FE FE FE FE FE FE FE FE FE FE FE
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FD FD FD FD FD FD FD FD FD FD FD FD FD FD FD FD
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
}
```

## Automatic Template Generation

Extend the previous single stage, pattern based algorithm using auto resolution:

```python
alg.auto_resolve_stage()
print(alg)
```

```text

0:{

template:{

________AaAaAaAa
_______aAaAaAaA_
______BbBbBbBb__
_____bBbBbBbB___
____CcCcCcCc____
___cCcCcCcC_____
__DdDdDdDd______
_dDdDdDdD_______

______AaAaAaAaAa
________________
____BbBbBbBbBb__
________________
__CcCcCcCcCc____
________________
DdDdDdDdDd______
________________
}

pseudo:{

______AaAaAaAaAa
____BbBbBbBbBb__
__CcCcCcCcCc____
DdDdDdDdDd______
________________
________________
________________
________________
}

map:{

00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FE FE FE FE FE FE FE FE FE FE FE FE FE FE FE FE
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FD FD FD FD FD FD FD FD FD FD FD FD FD FD FD FD
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
}

1:{

template:{

______AaAaAaAaAa
____AaAaAaAaAa__
__AaAaAaAaAa____
BbBbBbBbBb______
________________
________________
________________
________________

__AaAaAaAaAaAaAa
___AaAaAaAaAa___
________________
BbBbBbBbBb______
________________
________________
________________
________________
}

pseudo:{

__AaAaAaAaAaAaAa
___AaAaAaAaAa___
BbBbBbBbBb______
________________
________________
________________
________________
________________
}

map:{

00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
}

2:{

template:{

__AaAaAaAaAaAaAa
___aAaAaAaAaA___
AaAaAaAaAa______
________________
________________
________________
________________
________________

AaAaAaAaAaAaAaAa
_AaAaAaAaAaA____
________________
________________
________________
________________
________________
________________
}

pseudo:{

AaAaAaAaAaAaAaAa
_AaAaAaAaAaA____
________________
________________
________________
________________
________________
________________
}

map:{

00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
}

3:{

template:{

AaAaAaAaAaAaAaAa
_aAaAaAaAaAa____
________________
________________
________________
________________
________________
________________

AaAaAaAaAaAaAaAa
________________
________________
________________
________________
________________
________________
________________
}

pseudo:{

AaAaAaAaAaAaAaAa
________________
________________
________________
________________
________________
________________
________________
}

map:{

00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
}
```

## Complex Templates

Coming Soon

## Documentation

Resouces for usage, general theory and implementations can be found in [/docs/](https://github.com/EphraimCompEng/multiplier-lab/tree/master/docs).
For the API Reference head to multiplied's documentation [site](https://ephraimcompeng.github.io/multiplied/)


## Dependencies

Planned or currently in use.

| database                                           | visualization                        |
|:---------------------------------------------------|:-------------------------------------|
| [Parquet](https://github.com/apache/parquet-format)|[Matplotlib](https://matplotlib.org/ )|
| [Pandas](https://pandas.pydata.org/)               |                                      |

Full list TBD.
