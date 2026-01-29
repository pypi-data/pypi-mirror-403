# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nlp_tools_dataminer",  # Change this! Must be unique on PyPI
    version="0.1.1",
    author="Your Name",
    author_email="aryanjbagwe@gmail.com",
    description="A collection of NLP utility functions for education and prototyping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",  # Optional
    packages=["nlp_tools_dataminer"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Choose your license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "nltk",
        "spacy",
        "pandas",
    ],
    include_package_data=True,
)