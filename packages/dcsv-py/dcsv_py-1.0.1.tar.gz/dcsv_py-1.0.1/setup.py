from setuptools import setup, find_packages

setup(
    name="dcsv-py",
    version="1.0.1",
    description="Ultra High Performance, Stackless Discord Library for Python",
    author="DCSV Team",
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
    ],
)
