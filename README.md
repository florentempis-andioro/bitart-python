# bitart-python

A procedural integer art generator, ported to Python.

## Description

`bitart-python` creates procedural art by generating random integer functions that take pixel coordinates `(x, y)` and produce a color value. It avoids "boring" images by analyzing the output entropy and patterns.

This project is a Python port of the original Ruby implementation of `bitart`.

**Attribution**:
Found on mastodon https://freeradical.zone/@bitartbot/

Original code is available at https://gitlab.com/suetanvil/bitart

**Disclosure**:
This project has been **entirely vibecoded**. I don't claim any ownership of the original code, nor any "authority", "authorship", or "creativity" over the algorithm. All these go to @suetanvil (and the authors of the million lines of code Google has crawled to feed its LLM model, enabling it to generate this code)

I only added a few features:
- RGB & color gradient mode
- Command line interface
- Custom equation
- Custom color function

All of which have been 100% vibecoded.

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
# Generate a random image
python -m bitart -o output.png --depth 4

# Use RGB mode
python -m bitart -o rgb.png -c rgb

# Use a specific equation with a custom color gradient function
python -m bitart -o custom.png -e "x ^ y" -c orange
```

## License

This software is released under the **GNU Affero General Public License v3 (AGPLv3)** as it is entirely derivative of the original Ruby implementation.
See [LICENSE](LICENSE) for details.
