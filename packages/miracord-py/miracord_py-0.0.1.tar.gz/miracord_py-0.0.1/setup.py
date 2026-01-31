from setuptools import setup, find_packages

setup(
    name="miracord-py",
    version="0.0.1",
    author="Miracord Dev",
    description="Ultra High Performance, Stackless Discord Library for Python",
    long_description="A lightweight, raw-performance focused Discord library. No caching, raw events only.",
    long_description_content_type="text/markdown",
    url="https://github.com/seninkullaniciadın/miracord-py",
    packages=["miracord"],
    install_requires=[
        "aiohttp>=3.8.0",
        "websockets>=10.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
