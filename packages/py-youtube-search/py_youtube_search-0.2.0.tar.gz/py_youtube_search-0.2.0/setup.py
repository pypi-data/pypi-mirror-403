from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py-youtube-search",
    version="0.2.0",
    author="VishvaRam",  # <--- Change this
    author_email="murthyvishva@gmail.com",  # <--- Change this
    description="A lightweight, regex-based YouTube search library without API keys.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VishvaRam/py-youtube-search", # <--- Change this
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
