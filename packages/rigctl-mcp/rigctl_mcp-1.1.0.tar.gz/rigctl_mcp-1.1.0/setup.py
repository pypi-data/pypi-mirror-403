#!/usr/bin/env python3
from setuptools import setup

setup(
    name="rigctl-mcp",
    version="1.1.0",
    description="MCP server for Hamlib rigctl radio control",
    author="Zappatta",
    python_requires=">=3.10",
    py_modules=["server", "rigctl_client"],
    install_requires=[
        "mcp>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "rigctl-mcp=server:main",
        ],
    },
)
