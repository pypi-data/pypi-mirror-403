"""Setup configuration for MaxQuery package"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="maxquery",
    version="1.0.0",
    author="Chethan Patel",
    author_email="chethanpatel100@gmail.com",
    description="🚀 MaxCompute SQL Query Runner - Execute queries on Alibaba Cloud",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chethanpatel/maxquery",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "odps==3.5.1",
        "pandas==2.3.3",
        "python-dotenv==1.2.1",
        "pyarrow==23.0.0",
        "click>=8.0.0",
        "rich>=12.0.0",
    ],
    entry_points={
        "console_scripts": [
            "maxquery=maxquery.cli:main",
        ],
    },
    include_package_data=True,
)
