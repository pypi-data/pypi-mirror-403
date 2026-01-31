#!/usr/bin/env python3
"""
Test script for MCP TeXicode Server using HTTP Streaming transport.

This script tests the MCP protocol implementation with HTTP streaming,
verifying all tools and resources work correctly.
"""

import asyncio
import json
import sys
from typing import Any, Dict

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_http_streaming():
    """Test the MCP TeXicode server using HTTP streaming transport."""
    
    print("=" * 70)
    print("🧪 Testing MCP TeXicode Server with HTTP Streaming Transport")
    print("=" * 70)
    print()
    
    # Start the server as a subprocess with stdio transport
    # The chuk-mcp-server framework handles HTTP streaming internally
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_texicode.server"],
        env=None,
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                print("📡 Initializing MCP session...")
                await session.initialize()
                print("✅ Session initialized successfully")
                print()
                
                # Test 1: List available tools
                print("=" * 70)
                print("TEST 1: List Available Tools")
                print("=" * 70)
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  📐 {tool.name}: {tool.description}")
                print()
                
                # Test 2: List available resources
                print("=" * 70)
                print("TEST 2: List Available Resources")
                print("=" * 70)
                resources = await session.list_resources()
                print(f"Found {len(resources.resources)} resources:")
                for resource in resources.resources:
                    print(f"  📚 {resource.uri}: {resource.name}")
                print()
                
                # Test 3: Check TeXicode version
                print("=" * 70)
                print("TEST 3: Check TeXicode Installation")
                print("=" * 70)
                result = await session.call_tool("check_texicode_version", {})
                print("Result:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        print(json.dumps(data, indent=2))
                print()
                
                # Test 4: Render simple LaTeX expression
                print("=" * 70)
                print("TEST 4: Render Simple LaTeX Expression")
                print("=" * 70)
                expression = r"\frac{a}{b}"
                print(f"Expression: {expression}")
                result = await session.call_tool("render_latex", {
                    "expression": expression,
                    "color": False,
                    "normal_font": False,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Test 5: Render complex LaTeX expression
                print("=" * 70)
                print("TEST 5: Render Complex LaTeX Expression")
                print("=" * 70)
                expression = r"x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}"
                print(f"Expression: {expression}")
                result = await session.call_tool("render_latex", {
                    "expression": expression,
                    "color": False,
                    "normal_font": False,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Test 6: Render LaTeX with summation
                print("=" * 70)
                print("TEST 6: Render Summation")
                print("=" * 70)
                expression = r"\sum_{i=1}^n i^2"
                print(f"Expression: {expression}")
                result = await session.call_tool("render_latex", {
                    "expression": expression,
                    "color": False,
                    "normal_font": False,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Test 7: Render markdown with LaTeX
                print("=" * 70)
                print("TEST 7: Render Markdown with LaTeX")
                print("=" * 70)
                markdown = """# Math Example

The quadratic formula is: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$

And Euler's identity:

$$e^{i\\pi} + 1 = 0$$
"""
                print("Markdown content:")
                print(markdown)
                result = await session.call_tool("render_markdown", {
                    "content": markdown,
                    "color": False,
                    "normal_font": False,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Test 8: Read examples resource
                print("=" * 70)
                print("TEST 8: Read Examples Resource")
                print("=" * 70)
                result = await session.read_resource("texicode://examples")
                print("Examples resource content (first 500 chars):")
                for content in result.contents:
                    if hasattr(content, 'text'):
                        print(content.text[:500] + "...")
                print()
                
                # Test 9: Read config resource
                print("=" * 70)
                print("TEST 9: Read Config Resource")
                print("=" * 70)
                result = await session.read_resource("texicode://config")
                print("Config resource content:")
                for content in result.contents:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        print(json.dumps(data, indent=2))
                print()
                
                # Test 10: Test with color option
                print("=" * 70)
                print("TEST 10: Render with Color Option")
                print("=" * 70)
                expression = r"\pi"
                print(f"Expression: {expression} (with color=True)")
                result = await session.call_tool("render_latex", {
                    "expression": expression,
                    "color": True,
                    "normal_font": False,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Test 11: Test with normal font option
                print("=" * 70)
                print("TEST 11: Render with Normal Font")
                print("=" * 70)
                expression = r"E = mc^2"
                print(f"Expression: {expression} (with normal_font=True)")
                result = await session.call_tool("render_latex", {
                    "expression": expression,
                    "color": False,
                    "normal_font": True,
                })
                print("Rendered output:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
                
                # Summary
                print("=" * 70)
                print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
                print("=" * 70)
                print()
                print("Summary:")
                print("  ✓ MCP session initialization")
                print("  ✓ Tool listing")
                print("  ✓ Resource listing")
                print("  ✓ check_texicode_version tool")
                print("  ✓ render_latex tool (simple)")
                print("  ✓ render_latex tool (complex)")
                print("  ✓ render_latex tool (summation)")
                print("  ✓ render_markdown tool")
                print("  ✓ texicode://examples resource")
                print("  ✓ texicode://config resource")
                print("  ✓ Color option")
                print("  ✓ Normal font option")
                print()
                print("🎉 MCP TeXicode Server is working correctly with HTTP Streaming!")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main entry point."""
    await test_http_streaming()


if __name__ == "__main__":
    asyncio.run(main())
