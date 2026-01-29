from setuptools import setup, find_packages

setup(
    name="billingrails",
    version="0.1.0",
    description="Official Python SDK for Billingrails API - Flexible, composable, and intuitive API-first commerce platform",
    author="Billingrails",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
