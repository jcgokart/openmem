from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="openmem",
    version="0.1.1",
    author="jcgokart",
    author_email="",
    description="Memory System for AI-powered Development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openlyco/openmem",
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
        "cryptography>=3.0",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "omem=openmem.cli.main:main",
        ],
    },
    package_data={
        "openmem": ["py.typed"],
    },
)
