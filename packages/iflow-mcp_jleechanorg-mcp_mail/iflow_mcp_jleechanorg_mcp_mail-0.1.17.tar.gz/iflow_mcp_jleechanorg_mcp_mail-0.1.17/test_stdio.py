#!/usr/bin/env python3
"""Simple MCP stdio test script"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test MCP server with stdio transport"""
    # Start the server
    process = subprocess.Popen(
        ["/app/auto-mcp-upload/.venv/bin/python", "-m", "mcp_agent_mail.stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/app/auto-mcp-upload/data/2454"
    )

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test",
                "version": "1.0"
            }
        }
    }
    process.stdin.write(json.dumps(init_request) + "\n")
    process.stdin.flush()

    # Read initialization response
    init_response_line = process.stdout.readline()
    if init_response_line:
        print("Initialize response:", init_response_line.strip())
        try:
            init_response = json.loads(init_response_line)
            if "result" in init_response:
                # Send initialized notification
                initialized = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                process.stdin.write(json.dumps(initialized) + "\n")
                process.stdin.flush()

                # List tools
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                process.stdin.write(json.dumps(tools_request) + "\n")
                process.stdin.flush()

                # Read tools response
                tools_response_line = process.stdout.readline()
                if tools_response_line:
                    print("Tools response:", tools_response_line.strip())
                    try:
                        tools_response = json.loads(tools_response_line)
                        if "result" in tools_response and "tools" in tools_response["result"]:
                            tools = tools_response["result"]["tools"]
                            print(f"\n✅ Success! Found {len(tools)} tools")
                            print(f"Tool names: {[t.get('name', 'unknown') for t in tools[:10]]}")
                            return True
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse tools response: {e}")
            else:
                print(f"Initialize failed: {init_response}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse init response: {e}")
    else:
        print("No response from server")

    process.terminate()
    process.wait(timeout=5)
    return False

if __name__ == "__main__":
    try:
        success = test_mcp_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)