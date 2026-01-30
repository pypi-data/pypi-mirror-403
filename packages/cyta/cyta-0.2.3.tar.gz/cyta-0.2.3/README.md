# cyta

`cython -a` for terminal. No HTML, no browser.

## Usage

```bash
uvx cyta file.py                    # yellow = Python interaction
uvx cyta --annotate-fullc file.py   # show generated C code
uvx cyta --raw file.py              # plain text (no colors)
```

## Install

```bash
uv add cyta   # or: pip install cyta
```

## Example

```bash
$ cyta demo.py

demo.py
Yellow = Python interaction

  1 | import cython
  2 |
  3 | def slow_sum(data: list) -> float:  # highlighted yellow
  4 |     total = 0.0                      # highlighted yellow
  5 |     for x in data:                   # highlighted yellow
  6 |         total += x                   # highlighted yellow
  7 |     return total
```

## Name

**cy**thon **t**erminal **a**nnotation

## License

MIT
