"""
Setup script for the persistent-code-mcp package.
"""

from setuptools import setup, find_packages

# Read long description from README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="iflow-mcp_sparshdrolia_persistent-code",
    version="0.1.1",
    description="An MCP server for maintaining code knowledge across LLM chat sessions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/persistent-code-mcp",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.2.0",
        "llama-index-core>=0.9.0",
        "llama-index>=0.9.0",
        "llama-index-embeddings-huggingface>=0.1.0",
        "transformers>=4.34.0",
        "networkx>=3.1",
        "sentence-transformers>=2.2.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "fastapi>=0.103.0",
        "uvicorn>=0.23.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "persistent-code=persistent_code.__main__:main",
        ],
    },
)