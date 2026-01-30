"""
Setup script for faxter-clerk package.

This file provides backward compatibility for older pip versions.
Modern installations should use pyproject.toml.
"""

from setuptools import setup

# Read the contents of README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="faxter-clerk",
    version="1.0.0",
    description="Command-line interface for AI Accounting OS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Accounting Team",
    author_email="support@faxter.com",
    url="https://ai.faxter.com",
    packages=["faxter_clerk"],
    package_dir={"faxter_clerk": "."},
    py_modules=["clerk"],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "rich": ["rich>=13.0.0"],
        "sse": ["sseclient-py>=1.7.0"],
        "full": ["rich>=13.0.0", "sseclient-py>=1.7.0"],
    },
    entry_points={
        "console_scripts": [
            "clerk=faxter_clerk.clerk:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial :: Accounting",
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
    keywords="accounting ai cli finance bookkeeping natural-language",
)
