"""
Setup script for Telegram Group Scanner package.
"""

from setuptools import setup, find_packages
from pathlib import Path

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read long description safely
try:
    long_description = Path("README.md").read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = ""

setup(
    name="telegram-group-scanner",
    version="1.0.0",
    author="Telegram Scanner Team",
    description="A Python application for monitoring Telegram groups and extracting relevant information",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "telegram-scanner=telegram_scanner.cli:cli_main",
        ],
    },
)