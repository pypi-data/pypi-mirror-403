"""
Setup script for StegoVault
Advanced Steganography & Encryption Toolkit
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="stegovault",
    version="2.0.0",
    description="Advanced Steganography & Encryption Toolkit - Hide secrets inside images with military-grade encryption",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="StegoVault Contributors",
    license="MIT",
    url="https://github.com/yourusername/StegoVault",
    project_urls={
        "Documentation": "https://github.com/yourusername/StegoVault/blob/main/docs/",
        "Source": "https://github.com/yourusername/StegoVault",
        "Issues": "https://github.com/yourusername/StegoVault/issues",
        "Changelog": "https://github.com/yourusername/StegoVault/releases",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=requirements,
    extras_require={
        "gui": ["PyQt6>=6.5.0"],
        "web": ["Flask>=2.3.0", "Werkzeug>=2.3.0"],
        "all": ["PyQt6>=6.5.0", "Flask>=2.3.0", "Werkzeug>=2.3.0"],
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
    },
    entry_points={
        "console_scripts": [
            "stegovault=stegovault.cli_main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: System :: Archiving",
    ],
    keywords=[
        "steganography",
        "encryption",
        "security",
        "privacy",
        "image",
        "cryptography",
        "hiding",
    ],
    zip_safe=False,
)

