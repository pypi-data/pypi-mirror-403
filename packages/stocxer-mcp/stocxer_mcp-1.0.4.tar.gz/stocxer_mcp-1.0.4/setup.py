from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stocxer-mcp",
    version="1.0.4",
    author="Stocxer AI",
    description="MCP server for Stocxer AI Trading Platform - Connect your trading account to AI assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fdscoop/stocxer-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.9.0",
        "httpx>=0.27.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "stocxer-mcp=stocxer_mcp.server:cli",
        ],
    },
    include_package_data=True,
)
