"""Setup script for the jvdeploy package."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jvdeploy",
    version="0.1.0",
    description="Dockerfile generator for jvagent applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TrueSelph Inc.",
    author_email="adminh@trueselph.com",
    url="https://github.com/your-org/jvdeploy",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.9.0",
            "ruff>=0.1.0",
            "mypy>=1.6.0",
        ],
        "test": [
            "pytest>=7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jvdeploy=jvdeploy.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.8",
)
