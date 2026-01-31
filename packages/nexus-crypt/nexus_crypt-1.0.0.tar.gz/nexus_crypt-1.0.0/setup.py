from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nexus-crypt",
    version="1.0.0",
    author="Harshith Madhavaram",
    author_email="madhavaram.harshith2412@gmail.com",
    description="Post-quantum cryptographic suite with PFS, encryption, signatures, and hashing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Harshith2412/nexus-crypt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pycryptodome>=3.19.0",
        "pqcrypto>=0.1.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black", "mypy"],
    },
)