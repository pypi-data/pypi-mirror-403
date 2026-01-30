# sopel-urban

A Sopel IRC bot plugin for Urban Dictionary lookups.

> **Note:** This package was previously published as `sopel-modules.urban`.
> Please update your dependencies to use `sopel-urban` instead.

## Installation

```bash
pip install sopel-urban
```

## Usage

```
.urban <term>      - Look up a term on Urban Dictionary
.urban <term>/2    - Get the 2nd definition (1-10)
.ud <term>         - Alias for .urban
```

### Examples

```
.urban yeet
[urban] yeet - To discard an item at high velocity

.urban fronking/2
[urban] fronking - (2nd definition)
```

## Requirements

- Sopel 8.0+
- Python 3.8+

## License

MIT License
