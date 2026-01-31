from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="unepay-sdk",
    version="1.0.0",
    description="unepay sdk for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="astrafully",
    author_email="",
    url="https://github.com/astrafully/unepay-sdk",
    project_urls={
        "Bug Reports": "https://github.com/astrafully/unepay-sdk/issues",
        "Source": "https://github.com/astrafully/unepay-sdk",
    },
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.7",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="unepay payment api sdk",
)

