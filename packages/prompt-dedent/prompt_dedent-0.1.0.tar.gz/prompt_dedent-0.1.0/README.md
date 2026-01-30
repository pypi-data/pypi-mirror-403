# Dedent

A Python library for writing multi-line strings with proper indentation in your code, then automatically removing that indentation from the final string.

Perfect for **LLM prompts** and other multi-line strings that you want to keep properly indented within your code structure, especially when nested inside functions.

## Installation

```bash
pip install prompt_dedent
```

Or install from source:

```bash
git clone https://github.com/yourusername/dedent.git
cd dedent
pip install -e .
```

## Quick Start

```python
from prompt_dedent import dedent

text = dedent(
    """
    This is a multi-line string
    that can be indented in your code
    to match your code structure.
    """
)

print(text)
# Output:
# This is a multi-line string
# that can be indented in your code
# to match your code structure.
```

## Common Use Case: LLM Prompts

The typical use case for `dedent` is writing **LLM prompts** that are nested inside functions. Without `dedent`, you'd have to choose between messy unindented strings or awkward formatting. With `dedent`, you can write clean, properly indented prompts:

```python
from dedent import dedent

def analyze_message(message: str) -> dict:
    system_message = dedent(
        f"""
        Determine whether the following message includes a scheduling request.
        A scheduling request is defined as a scheduling inquiry that can be tied
        to a specific date, set of dates, or date range.
        
        Examples of scheduling requests:
            - this Saturday
            - next Friday
            - Tuesday, Feb 20th
            - August 25 - Sept 16
            - June 18th at 5pm
        
        Examples that are NOT scheduling requests:
            - saturday (without context)
            - friday (without context)
            - weekends
            - weekdays
        
        Return your response in the following format:
        {{
            "has_scheduling_request": bool
        }}
        """
    )
    
    # Use system_message with your LLM API...
    return {"has_scheduling_request": True}
```

Notice how the prompt stays properly indented within the function, making your code much more readable!

## Features

- **Automatic indentation removal**: Write strings with proper indentation that matches your code
- **Nested indentation support**: Create nested structures like bullet points
- **F-string insertion**: Insert multi-line variables into your dedented strings using the `insert()` function
- **Trailing whitespace removal**: Automatically removes trailing whitespace and empty lines

## Usage

### Basic Usage

```python
from dedent import dedent

message = dedent(
    """
    Hello, World!
    This is a nicely formatted message.
    """
)
```

### Nested Indentation

```python
from dedent import dedent

documentation = dedent(
    """
    Here's a list:
    
        - First item
        - Second item
            - Nested item
    """
)
```

### Inserting Variables with `insert()`

When you need to insert a multi-line string variable into your dedented text:

```python
from prompt_dedent import dedent, insert

inserted_text = """Line 1
Line 2
    - Indented line"""

result = dedent(
    f"""
    Here's some text:
        {insert(inserted_text)}
    And more text.
    """
)
```

### Preserving Trailing Whitespace

By default, trailing whitespace is removed. To preserve it:

```python
text = dedent(
    """
    Some text
    
    """,
    remove_trailing_whitespace=False
)
```

## Rules

1. **First line must be empty**: The string must start with a newline
2. **Second line determines base indentation**: The indentation of the second line is used as the base
3. **All content lines must have at least base indentation**: Lines with content must start with at least the base indentation
4. **Whitespace-only lines become empty**: Lines with only whitespace are converted to empty strings

## Tips

In VS Code, when you hit Enter inside a triple-quoted string, the default indentation is set to where the opening `"""` is. So this format is easiest:

```python
dedent(
    """
    Your text here.
    """
)
```

Rather than:

```python
dedent("""
    Your text here.
""")
```

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

