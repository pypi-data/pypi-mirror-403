#!/usr/bin/env python3

from setuptools import setup
import pathlib

# Get the long description from README
HERE = pathlib.Path(__file__).parent
long_description = (HERE / "README.md").read_text(encoding='utf-8') if (HERE / "README.md").exists() else "Leapfrog - Leap between development environments with ease"

setup(
    name="leapfrog-env",
    version="1.1.0",
    author="Yammers",
    author_email="adityap1172@gmail.com",
    description="🐸 Leap between development environments with ease",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/creepymarshmallow117/leapfrog",
    project_urls={
        "Bug Reports": "https://github.com/creepymarshmallow117/leapfrog/issues",
        "Source": "https://github.com/creepymarshmallow117/leapfrog",
        "Documentation": "https://github.com/creepymarshmallow117/leapfrog#readme",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="environment variables, development, cli, devops, configuration, env, dotenv, environment management",
    python_requires=">=3.7",
    py_modules=["leapfrog"],
    entry_points={
        "console_scripts": [
            "leapfrog=leapfrog:main",
        ],
    },
    install_requires=[
        # No external dependencies - pure Python stdlib
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "twine>=4.0",
            "build>=0.8",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)