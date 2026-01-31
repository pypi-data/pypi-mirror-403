from setuptools import setup, find_packages

setup(
    name="iflow-mcp_gomarble-ai_google-analytics-mcp-server",
    version="1.0.0",
    description="Google Analytics 4 MCP Server - FastMCP-powered Model Context Protocol server for Google Analytics 4 API integration",
    packages=find_packages(),
    py_modules=["server"],
    install_requires=[
        "fastmcp>=0.8.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "google-auth>=2.23.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "urllib3>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "google-analytics-mcp=server:main",
        ],
    },
    python_requires=">=3.10",
)
