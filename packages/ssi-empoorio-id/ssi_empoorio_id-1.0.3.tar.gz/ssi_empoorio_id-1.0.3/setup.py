"""
SSI Empoorio ID Python SDK Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ssi-empoorio-id",
    version="1.0.3",
    author="Empoorio Core Identity Team",
    author_email="sdk@empoorio.id",
    description="SSI Empoorio ID - Complete Self-Sovereign Identity SDK for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/empoorio/ssi-empoorio-id",
    project_urls={
        "Documentation": "https://docs.empoorio.id/python-sdk",
        "Source": "https://github.com/empoorio/ssi-empoorio-id",
        "Tracker": "https://github.com/empoorio/ssi-empoorio-id/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="ssi self-sovereign-identity verifiable-credentials web3 blockchain biometric quantum-resistant",
    packages=find_packages(where=".", exclude=["tests*", "docs*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "crypto": [
            "cryptography>=41.0.0",
            "pynacl>=1.5.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "httpx>=0.24.0",
        ],
        "dashboard": [
            "rich>=13.0.0",
            "click>=8.1.0",
            "pyperclip>=1.8.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "cryptography>=41.0.0",
            "pynacl>=1.5.0",
            "aiohttp>=3.8.0",
            "httpx>=0.24.0",
            "rich>=13.0.0",
            "click>=8.1.0",
            "pyperclip>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ssi-python=ssi_empoorio_id.cli:main",
            "ssi=ssi_empoorio_id.cli:main",  # Alias corto
        ],
    },
    include_package_data=True,
    zip_safe=False,
)