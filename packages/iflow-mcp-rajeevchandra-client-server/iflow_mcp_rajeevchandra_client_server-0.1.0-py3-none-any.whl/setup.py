from setuptools import setup, find_packages

setup(
    name="iflow-mcp-rajeevchandra-mcp_client_server_example",
    version="0.1.1",
    description="MCP Server example with add and multiply tools",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "math_server=math_server:main",
        ],
    },
    python_requires=">=3.11",
)