#!/usr/bin/env python3
"""
MCP TeXicode Server - LaTeX to Unicode art rendering for terminals.

This server wraps the TeXicode CLI tool to provide LaTeX rendering capabilities
through the Model Context Protocol (MCP).
"""

import asyncio
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from chuk_mcp_server import resource, run, tool

# Configure logging
logger = logging.getLogger(__name__)

# Global configuration
_COLOR_MODE_ENABLED = False
_ESCAPE_FILTERS_ENABLED = True


def strip_ansi_escape_sequences(text: str) -> str:
    """
    Remove ANSI escape sequences from text.
    
    This strips all ANSI escape codes including:
    - Color codes (e.g., ^[[38;5;232m)
    - Formatting codes (e.g., ^[[1m for bold)
    - Cursor movement codes
    - Other control sequences
    
    Args:
        text: Text potentially containing ANSI escape sequences
        
    Returns:
        Text with all ANSI escape sequences removed
    """
    # Pattern matches ANSI escape sequences: ESC [ ... m (and other variants)
    # This covers CSI (Control Sequence Introducer) sequences
    ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_escape_pattern.sub('', text)


@tool
async def render_latex(
    expression: str,
    color: bool | None = None,
    normal_font: bool = False,
) -> str:
    """
    Render a LaTeX expression to Unicode art using TeXicode.

    This tool converts LaTeX mathematical expressions into beautiful Unicode art
    that can be displayed directly in the terminal.

    Args:
        expression: LaTeX expression to render (e.g., '\\frac{a}{b}', '\\sum_{i=1}^n i^2')
        color: Enable color output (black on white). Default: False
        normal_font: Use normal font instead of serif. Default: False

    Returns:
        Unicode art representation of the LaTeX expression

    Examples:
        - Simple fraction: '\\frac{a}{b}'
        - Integral: '\\int_0^\\infty e^{-x^2} dx'
        - Summation: '\\sum_{i=1}^n i^2'
        - Quadratic formula: 'x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}'

    🧠 Auto-inferred: category=latex, tags=["tool", "latex", "math", "rendering"]
    """
    try:
        # Build the txc command
        cmd = ["txc"]
        
        # Use global color mode if color parameter is not explicitly set
        use_color = color if color is not None else _COLOR_MODE_ENABLED
        
        if use_color:
            cmd.append("-c")
        
        if normal_font:
            cmd.append("-n")
        
        # Add the expression (txc expects it as a positional argument)
        cmd.append(expression)
        
        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode("utf-8").strip()
            logger.error(f"TeXicode command failed: {error_msg}")
            return f"Error rendering LaTeX: {error_msg}"
        
        # Decode output
        output = stdout.decode("utf-8")
        
        # Apply escape sequence filtering if enabled
        if _ESCAPE_FILTERS_ENABLED:
            output = strip_ansi_escape_sequences(output)
        
        return output
        
    except FileNotFoundError:
        error_msg = (
            "TeXicode CLI (txc) not found. Please install it:\n"
            "  pipx install TeXicode\n"
            "or:\n"
            "  pip install TeXicode"
        )
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@tool
async def render_markdown(
    content: str,
    color: bool | None = None,
    normal_font: bool = False,
) -> str:
    """
    Process markdown content and render all LaTeX expressions within it.

    This tool takes markdown content with embedded LaTeX expressions and converts
    all the LaTeX to Unicode art, returning the processed markdown.

    Args:
        content: Markdown content with LaTeX expressions (inline with $ or blocks with $$)
        color: Enable color output (black on white). Default: False
        normal_font: Use normal font instead of serif. Default: False

    Returns:
        Processed markdown with LaTeX expressions rendered as Unicode art

    Examples:
        - Inline math: "The formula is $E = mc^2$"
        - Block math: "$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$"

    🧠 Auto-inferred: category=markdown, tags=["tool", "markdown", "latex", "rendering"]
    """
    try:
        # Create a temporary file for the markdown content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Build the txc command for markdown processing
            cmd = ["txc", "-f", tmp_path]
            
            # Use global color mode if color parameter is not explicitly set
            use_color = color if color is not None else _COLOR_MODE_ENABLED
            
            if use_color:
                cmd.append("-c")
            
            if normal_font:
                cmd.append("-n")
            
            # Execute the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8").strip()
                logger.error(f"TeXicode markdown processing failed: {error_msg}")
                return f"Error processing markdown: {error_msg}"
            
            # Decode output
            output = stdout.decode("utf-8")
            
            # Apply escape sequence filtering if enabled
            if _ESCAPE_FILTERS_ENABLED:
                output = strip_ansi_escape_sequences(output)
            
            return output
            
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
        
    except FileNotFoundError:
        error_msg = (
            "TeXicode CLI (txc) not found. Please install it:\n"
            "  pipx install TeXicode\n"
            "or:\n"
            "  pip install TeXicode"
        )
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@tool
async def check_texicode_version() -> dict:
    """
    Check if TeXicode is installed and return version information.

    This diagnostic tool verifies that the TeXicode CLI is properly installed
    and accessible.

    Returns:
        Dictionary with installation status and version information

    🧠 Auto-inferred: category=diagnostics, tags=["tool", "diagnostics", "version"]
    """
    try:
        # Try to run txc with a simple expression to verify it works
        process = await asyncio.create_subprocess_exec(
            "txc",
            "x",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {
                "installed": True,
                "status": "TeXicode CLI is installed and working",
                "test_output": stdout.decode("utf-8").strip(),
            }
        else:
            return {
                "installed": True,
                "status": "TeXicode CLI found but test failed",
                "error": stderr.decode("utf-8").strip(),
            }
        
    except FileNotFoundError:
        return {
            "installed": False,
            "status": "TeXicode CLI not found",
            "installation_instructions": (
                "Install TeXicode using:\n"
                "  pipx install TeXicode\n"
                "or:\n"
                "  pip install TeXicode"
            ),
        }
    except Exception as e:
        return {
            "installed": False,
            "status": "Error checking TeXicode",
            "error": str(e),
        }


@resource("texicode://examples")
async def get_examples() -> str:
    """
    Get example LaTeX expressions that can be rendered.

    🧠 Auto-inferred: mime_type=text/markdown, tags=["resource", "examples"]
    """
    return """# TeXicode Examples

## Basic Expressions

### Fractions
```latex
\\frac{a}{b}
\\frac{x^2 + y^2}{z}
```

### Exponents and Subscripts
```latex
x^2
a_i
x^{2n+1}
a_{i,j}
```

### Greek Letters
```latex
\\alpha, \\beta, \\gamma, \\delta
\\pi, \\theta, \\omega
\\Sigma, \\Delta, \\Omega
```

### Integrals
```latex
\\int_0^\\infty e^{-x^2} dx
\\int_a^b f(x) dx
\\iint_D f(x,y) dA
```

### Summations
```latex
\\sum_{i=1}^n i
\\sum_{i=1}^n i^2 = \\frac{n(n+1)(2n+1)}{6}
```

### Square Roots
```latex
\\sqrt{2}
\\sqrt{x^2 + y^2}
\\sqrt[3]{8}
```

### Limits
```latex
\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1
\\lim_{n \\to \\infty} (1 + \\frac{1}{n})^n = e
```

## Famous Formulas

### Quadratic Formula
```latex
x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}
```

### Euler's Identity
```latex
e^{i\\pi} + 1 = 0
```

### Pythagorean Theorem
```latex
a^2 + b^2 = c^2
```

### Gaussian Integral
```latex
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
```

### Taylor Series
```latex
e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!}
```

## Tips

- Wrap expressions in single quotes when using from command line
- Escape special characters like apostrophes: `f\\'(x)`
- Use `\\[ \\]`, `\\( \\)`, `$ $`, or `$$ $$` delimiters (optional)
- Most LaTeX math commands are supported
- Unsupported commands will show as `?`
"""


@resource("texicode://config")
async def get_config() -> dict:
    """
    Get server configuration and capabilities.

    🧠 Auto-inferred: mime_type=application/json, tags=["resource", "config"]
    """
    return {
        "server": "MCP TeXicode Server",
        "version": "0.1.0",
        "description": "LaTeX to Unicode art rendering for terminals",
        "capabilities": {
            "latex_rendering": True,
            "markdown_processing": True,
            "color_output": True,
            "font_options": ["serif", "normal"],
        },
        "tools": [
            {
                "name": "render_latex",
                "description": "Render LaTeX expression to Unicode art",
                "parameters": ["expression", "color", "normal_font"],
            },
            {
                "name": "render_markdown",
                "description": "Process markdown with LaTeX expressions",
                "parameters": ["content", "color", "normal_font"],
            },
            {
                "name": "check_texicode_version",
                "description": "Check TeXicode installation status",
                "parameters": [],
            },
        ],
        "resources": [
            {
                "uri": "texicode://examples",
                "description": "Example LaTeX expressions",
            },
            {
                "uri": "texicode://config",
                "description": "Server configuration",
            },
        ],
    }


def main() -> None:
    """
    Main entry point for the MCP TeXicode server.
    
    This function starts the server using the chuk-mcp-server framework.
    Configuration can be provided via:
    - Command-line arguments
    - Environment variables
    - Defaults (stdio transport, production settings)
    """
    import argparse
    import os
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="MCP TeXicode Server - LaTeX to Unicode art rendering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  MCP_TRANSPORT          Transport mode: 'stdio' or 'http' (default: stdio)
  MCP_HOST              Host to bind to for HTTP transport (default: 0.0.0.0)
  MCP_PORT              Port to bind to for HTTP transport (default: 8000)
  MCP_DEBUG             Enable debug mode: 'true' or 'false' (default: false)
  MCP_LOG_LEVEL         Logging level: DEBUG, INFO, WARNING, ERROR (default: WARNING)
  MCP_ENABLE_COLOR      Enable ANSI color output: 'true' or 'false' (default: false)
  MCP_NO_ESCAPE_FILTERS Disable escape sequence filtering: 'true' or 'false' (default: false)

Examples:
  # Run with stdio transport (default, for Claude Desktop)
  python -m mcp_texicode.server
  
  # Run with HTTP transport
  python -m mcp_texicode.server --transport http --port 8080
  
  # Run with debug mode
  python -m mcp_texicode.server --debug
  
  # Using environment variables
  MCP_TRANSPORT=http MCP_PORT=3000 python -m mcp_texicode.server
        """
    )
    
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        help="Transport mode (default: stdio, or MCP_TRANSPORT env var)"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to for HTTP transport (default: 0.0.0.0, or MCP_HOST env var)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to for HTTP transport (default: 8000, or MCP_PORT env var)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (default: false, or MCP_DEBUG=true env var)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: WARNING, or MCP_LOG_LEVEL env var)"
    )
    parser.add_argument(
        "--enable-color",
        action="store_true",
        help="Enable ANSI color output by default for all renders (default: false, or MCP_ENABLE_COLOR=true env var)"
    )
    parser.add_argument(
        "--no-escape-filters",
        action="store_true",
        help="Disable automatic filtering of ANSI escape sequences from output (default: false, or MCP_NO_ESCAPE_FILTERS=true env var)"
    )
    
    args = parser.parse_args()
    
    # Get configuration from args, then env vars, then defaults
    transport = args.transport or os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = args.host or os.getenv("MCP_HOST", "0.0.0.0")
    port = args.port or int(os.getenv("MCP_PORT", "8000"))
    debug = args.debug or os.getenv("MCP_DEBUG", "false").lower() == "true"
    log_level = args.log_level or os.getenv("MCP_LOG_LEVEL", "WARNING").upper()
    enable_color = args.enable_color or os.getenv("MCP_ENABLE_COLOR", "false").lower() == "true"
    no_escape_filters = args.no_escape_filters or os.getenv("MCP_NO_ESCAPE_FILTERS", "false").lower() == "true"
    
    # Set global configuration
    global _COLOR_MODE_ENABLED, _ESCAPE_FILTERS_ENABLED
    _COLOR_MODE_ENABLED = enable_color
    _ESCAPE_FILTERS_ENABLED = not no_escape_filters
    
    # Validate transport
    if transport not in ["stdio", "http"]:
        print(f"❌ Invalid transport: {transport}. Must be 'stdio' or 'http'")
        return
    
    # Print banner
    print("🎨 MCP TeXicode Server")
    print("=" * 70)
    print("LaTeX to Unicode art rendering for terminals")
    print("Built with chuk-mcp-server framework")
    print()
    print("Configuration:")
    print(f"  🚀 Transport: {transport}")
    if transport == "http":
        print(f"  🌐 Host: {host}")
        print(f"  🔌 Port: {port}")
    print(f"  🐛 Debug: {debug}")
    print(f"  📊 Log Level: {log_level}")
    print(f"  🎨 Color Mode: {enable_color}")
    print(f"  🧹 Escape Filters: {not no_escape_filters}")
    print()
    print("Available tools:")
    print("  📐 render_latex: Render LaTeX expressions to Unicode art")
    print("  📝 render_markdown: Process markdown with LaTeX expressions")
    print("  🔍 check_texicode_version: Check TeXicode installation")
    print()
    print("Available resources:")
    print("  📚 texicode://examples: Example LaTeX expressions")
    print("  ⚙️  texicode://config: Server configuration")
    print()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server with configured settings
    if transport == "stdio":
        run(transport="stdio", debug=debug)
    else:
        run(transport="http", host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
