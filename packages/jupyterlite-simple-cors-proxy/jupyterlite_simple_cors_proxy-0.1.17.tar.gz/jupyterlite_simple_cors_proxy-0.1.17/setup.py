# File: setup.py
from setuptools import setup, find_packages

setup(
    name="jupyterlite-simple-cors-proxy",
    version="0.1.17",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    author="Tony Hirst",
    author_email="tony.hirst@gmail.com",
    description="A simple CORS proxy utility with requests-like response",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/innovationOUtside/jupyterlite-simple-cors-proxy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)