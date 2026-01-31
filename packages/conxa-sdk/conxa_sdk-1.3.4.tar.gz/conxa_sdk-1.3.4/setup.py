"""
CONXA SDK - Setup Configuration

Install the SDK:
    pip install .

Install for development:
    pip install -e .[dev]
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="conxa-sdk",
    version="1.3.4",
    author="CONXA Team",
    author_email="support@conxa.in",
    description="Python SDK for integrating CONXA Wallet payments into AI services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/conxa/python-sdk",
    project_urls={
        "Documentation": "https://docs.conxa.in",
        "Bug Reports": "https://github.com/conxa/python-sdk/issues",
        "Source": "https://github.com/conxa/python-sdk",
    },
    packages=find_packages(exclude=["examples", "tests"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.32.0",
        "qrcode[pil]>=8.0.0",
        "Pillow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.32.0",
        ],
        "examples": [
            "flask>=2.0.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
    },
    keywords=[
        "conxa",
        "wallet",
        "payments",
        "ai",
        "tokens",
        "sdk",
        "api",
    ],
)
