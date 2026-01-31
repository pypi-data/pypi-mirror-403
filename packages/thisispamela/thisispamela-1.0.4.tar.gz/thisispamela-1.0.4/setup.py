"""
Setup script for Pamela Enterprise Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="thisispamela",
    version="1.0.4",
    author="Pamela",
    author_email="support@thisispamela.com",
    description="Pamela Enterprise Voice API SDK for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rtpam/pamela",
    packages=find_packages(),
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
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ],
)

