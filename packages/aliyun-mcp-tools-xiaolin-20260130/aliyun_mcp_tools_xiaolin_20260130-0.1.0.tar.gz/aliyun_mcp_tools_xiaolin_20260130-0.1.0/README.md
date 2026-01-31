# Aliyun MCP Tools Xiaolin

Basic MCP tools package for Aliyun, without system control or Bafayun functionality.

## Features

- **calculator**: Math calculation tool
- **get_current_time**: Get current system time
- **process_text**: Text processing tool with various operations

## Installation

```bash
pip install aliyun-mcp-tools-xiaolin-20260130
```

## Usage

### Basic Usage

```python
from aliyun_mcp_tools import calculator, get_current_time, process_text

# Calculate math expression
result = calculator("2 + 2 * 3")
print(result)  # Output: {"success": true, "result": 8}

# Get current time
current_time = get_current_time()
print(current_time)  # Output: {"success": true, "time": "2026-01-30 12:00:00"}

# Process text
text_result = process_text("hello world", "uppercase")
print(text_result)  # Output: {"success": true, "result": "HELLO WORLD"}
```

### Aliyun MCP Integration

```python
from mcp.server.mcpserver import MCPServer
from aliyun_mcp_tools import calculator, get_current_time, process_text

# Create MCP server
mcp = MCPServer("Aliyun Tools Server")

# Register tools
@mcp.tool()
def calculate(expression: str) -> dict:
    """Calculate math expression"""
    return calculator(expression)

@mcp.tool()
def get_time() -> dict:
    """Get current time"""
    return get_current_time()

@mcp.tool()
def text_process(text: str, operation: str) -> dict:
    """Process text with specified operation"""
    return process_text(text, operation)

# Run server
mcp.run(transport="stdio")
```

## Tools

### calculator
Calculates Python math expressions.

**Parameters:**
- `python_expression`: Python expression to evaluate

**Returns:**
- `{"success": true, "result": <calculated value>}` on success
- `{"success": false, "error": <error message>}` on failure

### get_current_time
Gets the current system time.

**Returns:**
- `{"success": true, "time": "YYYY-MM-DD HH:MM:SS"}` on success
- `{"success": false, "error": <error message>}` on failure

### process_text
Processes text with various operations.

**Parameters:**
- `text`: Text to process
- `operation`: Operation type ("uppercase", "lowercase", "capitalize", "count_words")

**Returns:**
- `{"success": true, "result": <processed text or word count>}` on success
- `{"success": false, "error": <error message>}` on failure

## Development

### Build the package

```bash
python -m build
```

### Upload to PyPI

```bash
python -m twine upload dist/*
```

## License

MIT License
