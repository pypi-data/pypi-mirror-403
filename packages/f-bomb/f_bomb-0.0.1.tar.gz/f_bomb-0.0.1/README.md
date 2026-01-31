[![Pylint](https://github.com/cgivre/f_bomb/actions/workflows/pylint.yml/badge.svg)](https://github.com/cgivre/f_bomb/actions/workflows/pylint.yml)
[![Tests](https://github.com/cgivre/f_bomb/actions/workflows/tests.yml/badge.svg)](https://github.com/cgivre/f_bomb/actions/workflows/tests.yml)

# F Bomb
If you've ever need to drop an F bomb in your code, we've got you covered. Drop a blunt, multilingual "F-bomb" in your Python code.

## Installation
```bash
pip install f_bomb
```

## Quick start
```python
from f_bomb import F_Bomb

bomb = F_Bomb()
print(str(bomb))          # FUCK!
print(bomb.drop("fr"))    # PUTAIN!
```

## Usage

### Choose a default language

```python
from f_bomb import F_Bomb

bomb = F_Bomb("de")
print(bomb.drop())        # SCHEISSE!
```

### Drop once in a specific language

```python
from f_bomb import F_Bomb

bomb = F_Bomb()
print(bomb.drop("it"))    # CAZZO!
```

### Carpet bomb (intentionally noisy)

```python
from f_bomb import F_Bomb

bomb = F_Bomb("en")
print(bomb.carpet_bomb())  # FUCK! plus a very large newline payload
```

## API

### `F_Bomb(language: str = "en")`
Creates a new bomb with a default language code.

### `drop(language: str | None = None) -> str`
Returns the uppercase expletive for the provided language code, or the default.

### `carpet_bomb(language: str | None = None, amount: int = 100) -> str`
Returns a single drop followed by a very large block of newlines.

## Supported language codes

The library ships with a list of language codes mapped to strong profanities.
Examples: `en`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `ja`, `ko`, `zh`.

## Notes

- Language codes are lowercased internally.
- Unknown language codes raise `KeyError`.

