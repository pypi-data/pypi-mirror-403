from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pygrammy",
    version="2.0.0",
    author="oscoder",
    description="Modern Telegram Bot Framework for Python - Inspired by GrammyJS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oscoderuz/pygrammy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "aiohttp>=3.8.0",
    ],
)