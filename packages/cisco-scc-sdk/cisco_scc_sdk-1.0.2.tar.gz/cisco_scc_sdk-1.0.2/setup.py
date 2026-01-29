"""
Setup configuration for Cisco Security Cloud Control SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cisco-scc-sdk",  # ← This is the PyPI package name
    version="1.0.2",
    author="Cisco Security",
    author_email="cisco-scc-sdk-team@cisco.com",
    description="Python SDK for Cisco Security Cloud Control Platform Management APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CiscoDevNet/cisco-scc-python-sdk",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
)
