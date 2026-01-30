from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="celery-chain-router",
    version="0.2.0",
    author="Petrit Avdylaj",
    author_email="petritavd@gmail.com",
    description="A Celery router that uses consistent hashing for data locality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/petritavd/celery-chain-router",
    project_urls={
        "Bug Tracker": "https://github.com/petritavd/celery-chain-router/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Celery",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.6",
    install_requires=[
        "celery>=5.0.0",
        "redis>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=20.8b1",
            "flake8>=3.8.0",
        ],
    },
) 