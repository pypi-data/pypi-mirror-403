from setuptools import setup, find_packages

setup(
    name="fragment-api-py",
    version="3.2.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
        "tonutils>=0.3.0",
        "pytoniq-core>=0.1.0"
    ],
    author="S1qwy",
    author_email="amirhansuper75@example.com",
    description="Python client for the Fragment API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/S1qwy/fragment-api-py",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
