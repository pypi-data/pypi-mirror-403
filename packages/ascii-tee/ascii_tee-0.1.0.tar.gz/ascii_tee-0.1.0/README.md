# ASCII Tee

Generate custom ASCII art t-shirts from the command line.

## Installation

```bash
pip install ascii-tee
```

## Usage

Interactive mode:

```bash
ascii-tee
```

With a prompt:

```bash
ascii-tee "a robot playing guitar"
```

### Options

- `--color`, `-c` - Shirt color: `black` or `white` (default: black)
- `--size`, `-s` - Shirt size: `S`, `M`, `L`, `XL`, `2XL` (default: L)
- `--qty`, `-q` - Quantity (default: 1)
- `--remove-background/-r` / `--keep-background/-R` - Control background dots
- `--no-preview` - Skip t-shirt preview
- `--open` - Open preview in browser
- `--checkout` - Skip confirmations, go directly to checkout

### Example

```bash
ascii-tee "vintage sunset" --color white --size M --qty 2
```
