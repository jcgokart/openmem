from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="trae-memory",
    version="2.0.0",
    author="OpenAlgo",
    author_email="",
    description="Memory System for Trae IDE",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trae-memory",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
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
        "pyyaml>=5.0",
        "jieba>=0.42",
    ],
    entry_points={
        "console_scripts": [
            "memory=memory.cli.main:main",
        ],
    },
    package_data={
        "memory": ["py.typed"],
    },
)
