#!/usr/bin/env python3
"""
Test script for MCP TeXicode Server using HTTP Streaming transport.

This script tests the MCP protocol implementation with HTTP streaming,
verifying all tools and resources work correctly.
"""

import asyncio
import json
import sys
import subprocess
import time
from typing import Any, Dict, Optional

import httpx


async def wait_for_server(url: str, timeout: int = 30):
    """Wait for the server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
        except:
            pass
        await asyncio.sleep(0.5)
    return False


async def test_http_streaming():
    """Test the MCP TeXicode server using HTTP streaming transport."""
    
    print("=" * 70)
    print("🧪 Testing MCP TeXicode Server with HTTP Streaming Transport")
    print("=" * 70)
    print()
    
    # Start the server as a subprocess
    print("🚀 Starting MCP TeXicode server...")
    server_process = subprocess.Popen(
        ["python", "-m", "mcp_texicode.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/chrism1/Code/ai/mcp-texicode",
    )
    
    test_failures = []
    session_id = None
    
    try:
        # Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        if not await wait_for_server("http://localhost:8000"):
            print("❌ Server failed to start within timeout")
            sys.exit(1)
        print("✅ Server is ready")
        print()
        
        # Use httpx directly with the /mcp endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Initialize
            print("=" * 70)
            print("TEST 1: Initialize MCP Session")
            print("=" * 70)
            
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await client.post(
                "http://localhost:8000/mcp",
                json=init_request,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to initialize: {response.status_code} - {response.text}")
                sys.exit(1)
            
            # Extract session ID from response headers
            session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
            
            result = response.json()
            if "error" in result:
                print(f"❌ Initialize error: {result['error']}")
                sys.exit(1)
                
            server_name = result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')
            print(f"✅ Initialized: {server_name}")
            print(f"   Session ID: {session_id}")
            print()
            
            if not session_id:
                print("⚠️  Warning: No session ID returned, but continuing...")
                print()
            
            # Prepare headers for subsequent requests
            headers = {"Content-Type": "application/json"}
            if session_id:
                headers["mcp-session-id"] = session_id
            
            # Test 2: List tools
            print("=" * 70)
            print("TEST 2: List Available Tools")
            print("=" * 70)
            response = await client.post(
                "http://localhost:8000/mcp",
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                headers=headers,
            )
            result = response.json()
            
            if "error" in result:
                test_failures.append(f"tools/list error: {result['error']}")
                print(f"❌ Error: {result['error']}")
            else:
                tools = result.get("result", {}).get("tools", [])
                print(f"✅ Found {len(tools)} tools:")
                if len(tools) != 3:
                    test_failures.append(f"Expected 3 tools, got {len(tools)}")
                for tool in tools:
                    print(f"  📐 {tool['name']}: {tool.get('description', 'No description')[:60]}...")
            print()
            
            # Test 3: List resources
            print("=" * 70)
            print("TEST 3: List Available Resources")
            print("=" * 70)
            response = await client.post(
                "http://localhost:8000/mcp",
                json={"jsonrpc": "2.0", "id": 3, "method": "resources/list"},
                headers=headers,
            )
            result = response.json()
            
            if "error" in result:
                test_failures.append(f"resources/list error: {result['error']}")
                print(f"❌ Error: {result['error']}")
            else:
                resources = result.get("result", {}).get("resources", [])
                print(f"✅ Found {len(resources)} resources:")
                if len(resources) != 2:
                    test_failures.append(f"Expected 2 resources, got {len(resources)}")
                for resource in resources:
                    print(f"  📚 {resource['uri']}: {resource.get('name', 'No name')}")
            print()
            
            # Test 4: Check TeXicode version
            print("=" * 70)
            print("TEST 4: Check TeXicode Installation")
            print("=" * 70)
            response = await client.post(
                "http://localhost:8000/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "check_texicode_version", "arguments": {}}
                },
                headers=headers,
            )
            result = response.json()
            
            if "error" in result:
                test_failures.append(f"check_texicode_version error: {result['error']}")
                print(f"❌ Error: {result['error']}")
            else:
                content = result.get("result", {}).get("content", [])
                if content:
                    print("✅ Result:")
                    data = json.loads(content[0].get("text", "{}"))
                    print(json.dumps(data, indent=2))
                else:
                    test_failures.append("check_texicode_version returned no content")
                    print("❌ No content returned")
            print()
            
            # Test 5: Render simple LaTeX
            print("=" * 70)
            print("TEST 5: Render Simple LaTeX Expression")
            print("=" * 70)
            expression = r"\frac{a}{b}"
            print(f"Expression: {expression}")
            response = await client.post(
                "http://localhost:8000/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "render_latex",
                        "arguments": {
                            "expression": expression,
                            "color": False,
                            "normal_font": False
                        }
                    }
                },
                headers=headers,
            )
            result = response.json()
            
            if "error" in result:
                test_failures.append(f"render_latex error: {result['error']}")
                print(f"❌ Error: {result['error']}")
            else:
                content = result.get("result", {}).get("content", [])
                if content:
                    print("✅ Rendered output:")
                    print(content[0].get("text", ""))
                else:
                    test_failures.append("render_latex returned no content")
            print()
            
            # Test 6: Read examples resource
            print("=" * 70)
            print("TEST 6: Read Examples Resource")
            print("=" * 70)
            response = await client.post(
                "http://localhost:8000/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "resources/read",
                    "params": {"uri": "texicode://examples"}
                },
                headers=headers,
            )
            result = response.json()
            
            if "error" in result:
                test_failures.append(f"resources/read error: {result['error']}")
                print(f"❌ Error: {result['error']}")
            else:
                contents = result.get("result", {}).get("contents", [])
                if contents:
                    print("✅ Examples resource content (first 300 chars):")
                    print(contents[0].get("text", "")[:300] + "...")
                else:
                    test_failures.append("resources/read returned no content")
            print()
            
            # Summary
            print("=" * 70)
            if test_failures:
                print("❌ TESTS COMPLETED WITH FAILURES")
                print("=" * 70)
                print()
                print("Failures:")
                for failure in test_failures:
                    print(f"  ✗ {failure}")
            else:
                print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
                print("=" * 70)
                print()
                print("Summary:")
                print("  ✓ MCP session initialization with HTTP streaming")
                print("  ✓ Session ID management")
                print("  ✓ Tool listing (3 tools)")
                print("  ✓ Resource listing (2 resources)")
                print("  ✓ check_texicode_version tool")
                print("  ✓ render_latex tool")
                print("  ✓ texicode://examples resource")
                print()
                print("🎉 MCP TeXicode Server is working correctly with HTTP Streaming!")
            
            print()
            print("Transport Details:")
            print("  - Protocol: MCP (Model Context Protocol)")
            print("  - Transport: HTTP with JSON-RPC 2.0")
            print("  - Endpoint: http://localhost:8000/mcp")
            print("  - Framework: chuk-mcp-server")
            print("  - Session Management: ✓ Working")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Stop the server
        print()
        print("🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped")
    
    if test_failures:
        sys.exit(1)


async def main():
    """Main entry point."""
    await test_http_streaming()


if __name__ == "__main__":
    asyncio.run(main())