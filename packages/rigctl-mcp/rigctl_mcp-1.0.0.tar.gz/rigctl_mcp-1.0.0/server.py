#!/usr/bin/env python3
"""
MCP Server for Rigctl (Hamlib) Radio Control.

This server provides tools to control SDR++ and other Hamlib-compatible
radio applications via the rigctl network protocol.
"""

import argparse
import asyncio
import json
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from rigctl_client import RigctlClient

app = Server("rigctl-mcp")

client: Optional[RigctlClient] = None

# CLI args (set by main())
default_host = "localhost"
default_port = 4532
auto_connect = False


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="connect",
            description="Connect to a rigctl server (Hamlib protocol)",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Rigctl host address (default: localhost)",
                        "default": "localhost"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Rigctl port (default: 4532)",
                        "default": 4532
                    }
                }
            }
        ),
        Tool(
            name="disconnect",
            description="Disconnect from the rigctl server",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_status",
            description="Get connection status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_frequency",
            description="Set the radio frequency in Hz",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequency_hz": {
                        "type": "integer",
                        "description": "Frequency in Hz (e.g., 88000000 for 88 MHz)"
                    }
                },
                "required": ["frequency_hz"]
            }
        ),
        Tool(
            name="get_frequency",
            description="Get the current radio frequency",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_mode",
            description="Set the demodulation mode and bandwidth",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["FM", "WFM", "AM", "USB", "LSB", "CW", "DSB", "RAW"],
                        "description": "Demodulation mode"
                    },
                    "bandwidth": {
                        "type": "integer",
                        "description": "Bandwidth in Hz (0 for automatic/default)",
                        "default": 0
                    }
                },
                "required": ["mode"]
            }
        ),
        Tool(
            name="get_mode",
            description="Get the current demodulation mode and bandwidth",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="start_recording",
            description="Start recording audio in SDR++ (or other rigctl-compatible software)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="stop_recording",
            description="Stop recording audio",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="tune_fm_station",
            description="Quick tune to an FM radio station (88-108 MHz)",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequency_mhz": {
                        "type": "number",
                        "description": "FM frequency in MHz (e.g., 88.5, 101.1)",
                        "minimum": 88,
                        "maximum": 108
                    },
                    "set_wfm_mode": {
                        "type": "boolean",
                        "description": "Automatically set to WFM mode (default: true)",
                        "default": True
                    }
                },
                "required": ["frequency_mhz"]
            }
        ),
        Tool(
            name="record_audio",
            description="Convenience tool: tune to frequency, set mode, and record for specified duration",
            inputSchema={
                "type": "object",
                "properties": {
                    "frequency_hz": {
                        "type": "integer",
                        "description": "Frequency in Hz"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["FM", "WFM", "AM", "USB", "LSB", "CW", "DSB", "RAW"],
                        "description": "Demodulation mode (optional)"
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Recording duration in seconds",
                        "minimum": 1,
                        "maximum": 3600
                    }
                },
                "required": ["frequency_hz", "duration_seconds"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global client

    if name == "connect":
        host = arguments.get("host", default_host)
        port = arguments.get("port", default_port)

        if client and client.socket:
            return [TextContent(
                type="text",
                text="Already connected. Disconnect first before connecting to a new server."
            )]

        client = RigctlClient(host=host, port=port)
        success = client.connect()
        if success:
            return [TextContent(
                type="text",
                text=f"Successfully connected to rigctl at {host}:{port}"
            )]
        else:
            client = None
            return [TextContent(
                type="text",
                text=f"Failed to connect to rigctl at {host}:{port}"
            )]

    if not client or not client.socket:
        return [TextContent(
            type="text",
            text="Not connected to rigctl. Use 'connect' tool first."
        )]

    if name == "disconnect":
        client.disconnect()
        client = None
        return [TextContent(type="text", text="Disconnected from rigctl")]

    elif name == "get_status":
        status = {
            "connected": bool(client and client.socket),
            "host": client.host if client else None,
            "port": client.port if client else None,
        }
        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "set_frequency":
        frequency_hz = arguments["frequency_hz"]
        success = client.set_frequency(frequency_hz)
        if success:
            return [TextContent(
                type="text",
                text=f"Set frequency to {frequency_hz} Hz ({frequency_hz / 1e6:.3f} MHz)"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to set frequency to {frequency_hz} Hz"
            )]

    elif name == "get_frequency":
        frequency = client.get_frequency()
        if frequency is not None:
            return [TextContent(
                type="text",
                text=f"Current frequency: {frequency} Hz ({frequency / 1e6:.3f} MHz)"
            )]
        else:
            return [TextContent(type="text", text="Failed to get frequency")]

    elif name == "set_mode":
        mode = arguments["mode"]
        bandwidth = arguments.get("bandwidth", 0)
        success = client.set_mode(mode, bandwidth)
        if success:
            return [TextContent(
                type="text",
                text=f"Set mode to {mode} with bandwidth {bandwidth} Hz"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to set mode to {mode}"
            )]

    elif name == "get_mode":
        mode_info = client.get_mode()
        if mode_info:
            mode, bandwidth = mode_info
            return [TextContent(
                type="text",
                text=f"Current mode: {mode}, bandwidth: {bandwidth} Hz"
            )]
        else:
            return [TextContent(type="text", text="Failed to get mode")]

    elif name == "start_recording":
        success = client.start_recording()
        if success:
            return [TextContent(
                type="text",
                text="Started recording. Audio will be saved to the application's recording directory."
            )]
        else:
            return [TextContent(type="text", text="Failed to start recording")]

    elif name == "stop_recording":
        success = client.stop_recording()
        if success:
            return [TextContent(
                type="text",
                text="Stopped recording. Check the application's recording directory for the file."
            )]
        else:
            return [TextContent(type="text", text="Failed to stop recording")]

    elif name == "tune_fm_station":
        frequency_mhz = arguments["frequency_mhz"]
        set_wfm = arguments.get("set_wfm_mode", True)

        frequency_hz = int(frequency_mhz * 1e6)

        # Set frequency
        if not client.set_frequency(frequency_hz):
            return [TextContent(
                type="text",
                text=f"Failed to set frequency to {frequency_mhz} MHz"
            )]

        # Set WFM mode if requested
        if set_wfm:
            if not client.set_mode("WFM", 200000):
                return [TextContent(
                    type="text",
                    text=f"Set frequency to {frequency_mhz} MHz but failed to set WFM mode"
                )]

        # Verify
        actual_freq = client.get_frequency()
        if actual_freq:
            return [TextContent(
                type="text",
                text=f"Tuned to {actual_freq / 1e6:.3f} MHz FM" + (" in WFM mode" if set_wfm else "")
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Tuned to {frequency_mhz} MHz FM" + (" in WFM mode" if set_wfm else "")
            )]

    elif name == "record_audio":
        frequency_hz = arguments["frequency_hz"]
        mode = arguments.get("mode")
        duration = arguments["duration_seconds"]

        # Set frequency
        if not client.set_frequency(frequency_hz):
            return [TextContent(
                type="text",
                text=f"Failed to set frequency to {frequency_hz} Hz"
            )]

        # Set mode if provided
        if mode:
            if not client.set_mode(mode, 0):
                return [TextContent(
                    type="text",
                    text=f"Set frequency but failed to set mode to {mode}"
                )]

        # Start recording
        if not client.start_recording():
            return [TextContent(type="text", text="Failed to start recording")]

        # Wait for duration
        await asyncio.sleep(duration)

        # Stop recording
        if not client.stop_recording():
            return [TextContent(type="text", text="Started recording but failed to stop it properly")]

        return [TextContent(
            type="text",
            text=f"Recorded {duration} seconds at {frequency_hz / 1e6:.3f} MHz" + (f" in {mode} mode" if mode else "")
        )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _async_main():
    global client

    # Auto-connect if requested
    if auto_connect:
        client = RigctlClient(host=default_host, port=default_port)
        if client.connect():
            import sys
            print(f"Auto-connected to rigctl at {default_host}:{default_port}", file=sys.stderr)
        else:
            client = None
            import sys
            print(f"Warning: Failed to auto-connect to {default_host}:{default_port}", file=sys.stderr)

    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    global default_host, default_port, auto_connect

    parser = argparse.ArgumentParser(description="MCP server for Hamlib rigctl radio control")
    parser.add_argument("--host", default="localhost", help="Rigctl server host (default: localhost)")
    parser.add_argument("--port", type=int, default=4532, help="Rigctl server port (default: 4532)")
    parser.add_argument("--auto-connect", action="store_true", help="Automatically connect to rigctl on startup")

    args = parser.parse_args()

    default_host = args.host
    default_port = args.port
    auto_connect = args.auto_connect

    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
