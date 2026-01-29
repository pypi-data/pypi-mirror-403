from setuptools import setup, find_packages

setup(
    name="wrapx",
    version="0.0.1",
    description="Standardized API response envelopes using Pydantic",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Til Schwarze",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0",
    ],
    license="MIT",
)
