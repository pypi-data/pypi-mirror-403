from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="faker-ru-pii",
    version="0.1.0",
    author="Ivan Boldyrev",
    author_email="iaboldyrev032@gmail.com",
    description="Faker provider for Russian PII data generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ivanboldyrevv/faker-ru-pii",
    packages=find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "Faker>=39.0.0",
    ],
)
