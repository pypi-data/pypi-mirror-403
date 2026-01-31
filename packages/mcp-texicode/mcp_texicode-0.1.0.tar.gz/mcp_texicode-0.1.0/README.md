# MCP TeXicode Server

A Model Context Protocol (MCP) server that provides LaTeX to Unicode art rendering capabilities using [TeXicode](https://github.com/mkhan45/TeXicode).

Built with the [chuk-mcp-server](https://github.com/chrishayuk/chuk-mcp-server) framework for zero-configuration deployment.

## Features

- 📐 **render_latex**: Convert LaTeX expressions to beautiful Unicode art
- 📝 **render_markdown**: Process markdown files with embedded LaTeX expressions
- 🔍 **check_texicode_version**: Verify TeXicode installation
- 📚 **Resources**: Example LaTeX expressions and server configuration
- ⚙️ **Flexible Configuration**: CLI args, environment variables, or defaults

## Demo

Here's example of what this project can do.  First, configure the MCP server with your agentic coding tool of choice, eg. IBM Bob, Claude Code, Codex, etc. and make sure mcp-texicode appears in the mcp servers list.

Send a prompt like the following example.

Prompt:

```text
   What are your Top 10 favorite extremely complex mathematical equations (using LaTex and texicode tools for formatting)?
```

Output:

```text

   Here are my Top 10 favorite extremely complex mathematical equations, beautifully rendered using TeXicode:

   1. Einstein Field Equations (General Relativity)
    1      1            8π𝐺
    2 𝑅  -╶─╴𝑅𝑔  +Λ𝑔  =╶───╴𝑇
    3  μν  2   μν   μν  𝑐⁴   μν

   2. Navier-Stokes Equations (Fluid Dynamics)
    1  ⎛ ∂𝐯      ⎞
    2 ρ⎜╶──╴+𝐯⋅∇𝐯⎟=-∇𝑝+μ∇²𝐯+𝐟
    3  ⎝ ∂𝑡      ⎠

   3. Riemann Zeta Function (Analytic Number Theory)
    1       ∞
    2      ┰─╴ 1     ┰─┰     1
    3 ζ(𝑠)=▐╸ ╶──╴=  ┃ ┃  ╶─────╴,  ℜ(𝑠)>1
    4      ┸─╴ 𝑛ˢ    ┸ ┸   1-𝑝⁻ˢ
    5      ⁿ⁼¹     𝑝 prime

   4. Schrödinger Equation (Quantum Mechanics)
    1    ∂         ⎡  ℏ²          ⎤
    2 𝑖ℏ╶──╴Ψ(𝐫,𝑡)=⎢-╶──╴∇²+𝑉(𝐫,𝑡)⎥Ψ(𝐫,𝑡)
    3    ∂𝑡        ⎣  2𝑚          ⎦

   5. Cauchy-Riemann Equations (Complex Analysis)
    1  ∂𝑢   ∂𝑣     ∂𝑢    ∂𝑣
    2 ╶──╴=╶──╴,  ╶──╴=-╶──╴
    3  ∂𝑥   ∂𝑦     ∂𝑦    ∂𝑥

   6. Yang-Mills Equations (Gauge Theory)
    1    μν  ν
    2 𝐷 𝐹  =𝐽 ,  𝐹  =∂ 𝐴 -∂ 𝐴 -𝑖𝑔[𝐴 ,𝐴 ]
    3  μ          μν  μ ν  ν μ     μ  ν

   7. Atiyah-Singer Index Theorem (Differential Geometry)
    1        ⌠
    2 ind(𝐷)=│ 𝐴̂(𝑇𝑀)∧ch(𝐸)
    3        ⌡
    4         ᴹ

   8. Ramanujan's Master Theorem
    1  ∞     ∞
    2 ⌠     ┰─╴ ϕ(𝑛)(-𝑥)ⁿ
    3 │ 𝑥ˢ⁻¹▐╸ ╶─────────╴𝑑𝑥=Γ(𝑠)ϕ(-𝑠)
    4 ⌡₀    ┸─╴    𝑛!
    5       ⁿ⁼⁰

   9. Gauss-Bonnet Theorem (Differential Geometry)
    1 ⌠      ⌠
    2 │ 𝐾 𝑑𝐴+│  𝑘  𝑑𝑠=2πχ(𝑀)
    3 ⌡      ⌡   ᵍ
    4  ᴹ      ∂𝑀

   10. Dirac Equation (Relativistic Quantum Mechanics)
    1    μ
    2 (𝑖γ ∂ -𝑚)ψ=0
    3      μ

   Each equation is now rendered in beautiful Unicode mathematical notation using the TeXicode rendering engine!
```

## Installation

### Prerequisites

1. **Install TeXicode CLI** (required):
   ```bash
   # Using pipx (recommended)
   pipx install TeXicode
   
   # Or using pip
   pip install TeXicode
   ```

2. **Install mcp-texicode**:
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/mcp-texicode.git
   cd mcp-texicode
   
   # Install dependencies
   pip install -e .
   ```

## Configuration

The server supports multiple configuration methods (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

### Command-Line Arguments

```bash
python -m mcp_texicode.server [OPTIONS]

Options:
  --transport {stdio,http}     Transport mode (default: stdio)
  --host HOST                  Host for HTTP transport (default: 0.0.0.0)
  --port PORT                  Port for HTTP transport (default: 8000)
  --debug                      Enable debug mode (default: false)
  --log-level {DEBUG,INFO,WARNING,ERROR}
                              Logging level (default: WARNING)
  --no-escape-filters          Disable ANSI escape sequence filtering (default: enabled)
  -h, --help                   Show help message
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport mode: `stdio` or `http` | `stdio` |
| `MCP_HOST` | Host to bind to (HTTP only) | `0.0.0.0` |
| `MCP_PORT` | Port to bind to (HTTP only) | `8000` |
| `MCP_DEBUG` | Enable debug mode: `true` or `false` | `false` |
| `MCP_LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `WARNING` |
| `MCP_NO_ESCAPE_FILTERS` | Disable ANSI escape sequence filtering: `true` or `false` | `false` |

### Usage Examples

#### 1. Default Configuration (stdio for Claude Desktop)

```bash
python -m mcp_texicode.server
```

This uses stdio transport, which is the standard for MCP clients like Claude Desktop.

#### 2. HTTP Transport with Custom Port

```bash
python -m mcp_texicode.server --transport http --port 8080
```

Or using environment variables:

```bash
MCP_TRANSPORT=http MCP_PORT=8080 python -m mcp_texicode.server
```

#### 3. Debug Mode

```bash
python -m mcp_texicode.server --debug --log-level DEBUG
```

Or using environment variables:

```bash
MCP_DEBUG=true MCP_LOG_LEVEL=DEBUG python -m mcp_texicode.server
```

#### 4. Production HTTP Server

```bash
python -m mcp_texicode.server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level WARNING
```

## Claude Desktop Configuration

To use with Claude Desktop, add to your `claude_desktop_config.json`:

### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Examples

#### 1. Using uv with Local Clone (Recommended for Development)

If you've cloned the repository locally and want to use `uv` for dependency management:

```json
{
  "mcpServers": {
    "texicode": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-texicode",
        "run",
        "mcp-texicode"
      ]
    }
  }
}
```

**Note:** Replace `/absolute/path/to/mcp-texicode` with the actual path to your cloned repository.

**Example paths:**
- macOS/Linux: `"/Users/username/Code/mcp-texicode"`
- Windows: `"C:\\Users\\username\\Code\\mcp-texicode"`

#### 2. Using uv with Installed Package

If you've installed mcp-texicode via pip/uv:

```json
{
  "mcpServers": {
    "texicode": {
      "command": "uvx",
      "args": ["mcp-texicode"]
    }
  }
}
```

#### 3. Using Python Directly

```json
{
  "mcpServers": {
    "texicode": {
      "command": "python",
      "args": ["-m", "mcp_texicode.server"]
    }
  }
}
```

#### 4. With Custom Configuration (Environment Variables)

```json
{
  "mcpServers": {
    "texicode": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-texicode",
        "run",
        "mcp-texicode"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_DEBUG": "false"
      }
    }
  }
}
```

#### 5. With Custom Configuration (CLI Arguments)

```json
{
  "mcpServers": {
    "texicode": {
      "command": "python",
      "args": [
        "-m",
        "mcp_texicode.server",
        "--transport",
        "stdio",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

#### 6. Using Virtual Environment

If you have a specific virtual environment:

```json
{
  "mcpServers": {
    "texicode": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "mcp_texicode.server"]
    }
  }
}
```

### Verifying Configuration

After updating your configuration:

1. **Restart Claude Desktop** completely (quit and reopen)
2. **Check the MCP icon** in Claude Desktop - it should show the texicode server
3. **Test a tool** by asking Claude to render a LaTeX expression

Example prompt to test:
```
Can you render the quadratic formula using the texicode server?
```

## Output Filtering

By default, the server **filters ANSI escape sequences** from TeXicode output to provide clean Unicode art. This is because the TeXicode CLI (`txc`) can output color formatting codes that may not be desired in all contexts.

### Why Filtering?

- **Without filtering**: `txc -c "x^2"` outputs 30 bytes including ANSI color codes: `\x1b[38;5;232m\x1b[48;5;255mx²\x1b[0m`
- **With filtering** (default): Same expression outputs clean 4 bytes: `x²`

### Disabling Filters

If you want to preserve ANSI escape sequences (e.g., for color output in terminals that support it):

**Using CLI argument:**
```bash
python -m mcp_texicode.server --no-escape-filters
```

**Using environment variable:**
```bash
MCP_NO_ESCAPE_FILTERS=true python -m mcp_texicode.server
```

**In Claude Desktop config:**
```json
{
  "mcpServers": {
    "texicode": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-texicode",
        "run",
        "mcp-texicode",
        "--no-escape-filters"
      ]
    }
  }
}
```

## Available Tools

### render_latex

Render a LaTeX expression to Unicode art.

**Parameters:**
- `expression` (string, required): LaTeX expression to render
- `color` (boolean, optional): Enable color output (default: false)
- `normal_font` (boolean, optional): Use normal font instead of serif (default: false)

**Example:**
```python
# In Claude Desktop or MCP client
render_latex(expression="\\frac{a}{b}")
render_latex(expression="\\int_0^\\infty e^{-x^2} dx", color=True)
```

### render_markdown

Process markdown content with embedded LaTeX expressions.

**Parameters:**
- `content` (string, required): Markdown content with LaTeX expressions
- `color` (boolean, optional): Enable color output (default: false)
- `normal_font` (boolean, optional): Use normal font instead of serif (default: false)

**Example:**
```python
render_markdown(content="The formula is $E = mc^2$")
```

### check_texicode_version

Check if TeXicode is installed and working.

**Returns:** Dictionary with installation status and version information.

## Available Resources

### texicode://examples

Get example LaTeX expressions that can be rendered.

### texicode://config

Get server configuration and capabilities.

## LaTeX Examples

### Basic Expressions

```latex
# Fractions
\frac{a}{b}

# Exponents and subscripts
x^2, a_i

# Greek letters
\alpha, \beta, \gamma, \pi

# Integrals
\int_0^\infty e^{-x^2} dx

# Summations
\sum_{i=1}^n i^2

# Square roots
\sqrt{x^2 + y^2}
```

### Famous Formulas

```latex
# Quadratic formula
x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}

# Euler's identity
e^{i\pi} + 1 = 0

# Gaussian integral
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
mcp-texicode/
├── src/
│   └── mcp_texicode/
│       ├── __init__.py
│       └── server.py          # Main server implementation
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Transport Modes

### stdio (Default)

- **Use case**: MCP clients like Claude Desktop
- **Protocol**: JSON-RPC over stdin/stdout
- **Configuration**: No network configuration needed
- **Best for**: Desktop applications, CLI tools

### http

- **Use case**: Web services, remote access, testing
- **Protocol**: HTTP with Server-Sent Events (SSE)
- **Configuration**: Requires host and port
- **Best for**: Web applications, microservices, debugging

## Troubleshooting

### TeXicode Not Found

If you get an error about TeXicode not being installed:

```bash
# Install TeXicode
pipx install TeXicode

# Verify installation
txc "x^2"
```

### Port Already in Use (HTTP mode)

If the port is already in use, specify a different port:

```bash
python -m mcp_texicode.server --transport http --port 8080
```

### Debug Mode

Enable debug mode to see detailed logs:

```bash
python -m mcp_texicode.server --debug --log-level DEBUG
```

## License

MIT License - see LICENSE file for details.

## Credits

- Built with [chuk-mcp-server](https://github.com/chrishayuk/chuk-mcp-server)
- Uses [TeXicode](https://github.com/mkhan45/TeXicode) for LaTeX rendering
- Implements the [Model Context Protocol](https://modelcontextprotocol.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
