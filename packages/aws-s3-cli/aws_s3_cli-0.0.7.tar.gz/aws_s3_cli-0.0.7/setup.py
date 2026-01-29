from setuptools import setup, find_packages

def readme():
    with open("README.md", encoding="utf-8") as f:
        return f.read()

setup(
    name="aws-s3-cli",
    version="0.0.7",
    description="Upload, download, check file availability, and list files from AWS S3 bucket",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sujitmandal/aws-s3-cli",
    author="Sujit Mandal",
    author_email="mandals974@gmail.com",
    license="MIT",

    python_requires=">=3.7",

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],

    install_requires=[
        "boto3>=1.20"
    ],

    packages=find_packages(),
    include_package_data=True,
)
