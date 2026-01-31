from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="dcsv-py",
    version="1.0.3",
    description="Ultra High Performance, Stackless Discord Library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DCSV Team",
    author_email="you@example.com",
    url="https://github.com/DiscordSunucu/dcsv-py",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "websockets>=11.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
