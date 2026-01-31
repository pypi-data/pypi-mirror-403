"""
Setup script for Quantum Hydra Cipher Package
"""

from setuptools import setup
import os

# Read README for long description
def read_file(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="quantum-hydra-cipher",
    version="3.0.0",
    author="Muhammad Sufiyan Baig",
    author_email="send.sufiyan@gmail.com",
    description="A 7-layer encryption system supporting multiple file formats",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quantum-hydra",
    license="MIT",
    py_modules=["quantum_hydra"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    entry_points={
        "console_scripts": [
            "quantum-hydra=quantum_hydra:main",
            "qhc=quantum_hydra:main",
        ],
    },
    keywords=[
        "encryption",
        "cipher",
        "security",
        "cryptography",
        "multi-layer",
        "file-encryption",
        "pdf",
        "image",
        "video",
        "audio",
    ],
    project_urls={
        "Homepage": "https://github.com/yourusername/quantum-hydra",
        "Documentation": "https://github.com/yourusername/quantum-hydra#readme",
        "Bug Reports": "https://github.com/yourusername/quantum-hydra/issues",
        "Source": "https://github.com/yourusername/quantum-hydra",
        "Changelog": "https://github.com/yourusername/quantum-hydra/blob/main/CHANGELOG.md",
    },
    include_package_data=True,
    zip_safe=False,
)
