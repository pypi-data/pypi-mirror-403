from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding='utf-8')

setup(
    name="abhanti",
    version="1.0.0",
    author="Abhishek",
    author_email="abhishek@example.com",
    description="Universal AI Client - Works out of the box with FREE endpoint",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/abhanti",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "httpx>=0.24.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "langchain": ["langchain-core>=0.1.0"],
    },
    keywords="ai llm openai free universal-client",
)
