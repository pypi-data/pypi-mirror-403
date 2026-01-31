from setuptools import setup, find_packages

setup(
    name="iflow-mcp_organicmoron_sp-mcp",
    version="1.0.1",
    description="Bridge between Super Productivity and MCP (Model Context Protocol) servers for Claude Desktop integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="organicmoron",
    packages=[],
    py_modules=["mcp_server"],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sp-mcp=mcp_server:main",
        ],
    },
)