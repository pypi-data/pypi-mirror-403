from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pillod",
    version="0.2.0",
    author="DRTB",
    author_email="darealtrueblue.contact@gmail.com",
    description="A comprehensive Python utility library with 100+ functions across 9 modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DaRealTrueBlue/pillod",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    keywords="utilities tools parser string math list validators date random file config",
    project_urls={
        "Bug Reports": "https://github.com/DaRealTrueBlue/pillod/issues",
        "Source": "https://github.com/DaRealTrueBlue/pillod",
    },
)
