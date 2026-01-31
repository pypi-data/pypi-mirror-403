from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="iflow-mcp-nikmaniatis-pd-mcp-server",
    version="0.1.2",
    author="nikmaniatis",
    description="A Model Context Protocol (MCP) server for Pure Data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["main", "mcp_server", "osc_daemon"],
    python_requires=">=3.11",
    install_requires=[
        "argparse>=1.4.0",
        "asyncio>=3.4.3",
        "jsonschema>=4.23.0",
        "mcp[cli]>=1.4.1",
        "python-osc>=1.9.3",
    ],
    entry_points={
        'console_scripts': [
            'pd-mcp-server=main:main',
        ],
    },
)