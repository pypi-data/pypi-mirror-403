from setuptools import setup, find_packages

setup(
    name="stockai-sdk",
    version="1.0.0",
    author="Stock AI Dev",
    description="SDK for Stock AI Protected Endpoints",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
)