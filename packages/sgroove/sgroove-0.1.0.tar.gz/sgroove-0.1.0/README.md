# sgroove

`sgroove` is a Python library for styling terminal output using ANSI escape sequences. It provides a fluent interface and integrates with Python's f-string formatting.

This started as a small personal project to explore the `__format__`-Dunder-method but might be useful for someone else, too.

### Features

`sgroove` provides a fluent interface that lets you build up formatting step by step by chaining style calls, which keeps even more complex combinations readable and easy to reuse. It also integrates with Python’s f-string formatting so you can apply styles inline via semicolon-separated format specifiers, making it convenient to style output without wrapping everything in separate function calls.

#### Supported Colors

For colors, it supports the full range of common terminal options: the 8 standard ANSI colors with bright variants for quick, named styling, the 256-color ANSI palette for finer-grained choices, and 24-bit TrueColor (RGB) for exact color control when your terminal supports it.

| Name | Bright Variant |
| :--- | :--- |
| `black` | `bright_black` |
| `red` | `bright_red` |
| `green` | `bright_green` |
| `yellow` | `bright_yellow` |
| `blue` | `bright_blue` |
| `magenta` | `bright_magenta` |
| `cyan` | `bright_cyan` |
| `white` | `bright_white` |

#### Supported Styles

 In addition to colors, it includes widely used text modifiers—such as bold, italic, and underline—so you can highlight headings, warnings, and status messages consistently in CLI output.

| Specifier | Description |
| :--- | :--- |
| `bold` | Bold or increased intensity |
| `faint` | Decreased intensity |
| `italic` | Italic font |
| `underlined` | Underlined text |
| `blinking` | Blinking text |
| `crossed_out` | Strikethrough |
| `framed` | Framed text |
| `encircled` | Encircled text |
| `overlined` | Overlined text |

### Examples

#### Fluent Interface

The fluent interface allows you to build styles by chaining method calls on an `AnsiStr` object.

```python
from sgroove import S

# Simple red text
print(S("Hello").fg("red"))

# Bold and green background
print(S("Success").bold().bg("green"))

# Using RGB colors
print(S("TrueColor").rgb(255, 165, 0)) # Orange
```

#### Format Version

`sgroove` objects can be styled directly within f-strings using the format specifier. Multiple styles can be combined using semicolons.

```python
from sgroove import S

text = S("Hello World!")

# Applying basic colors and styles
print(f"{text:blue;bold;underlined}")

# Using RGB in f-strings
print(f"{text:rgb(0, 255, 128)}")

# Combining named colors and custom RGB background
print(f"{text:white;bg_rgb(50, 50, 50)}")
```
