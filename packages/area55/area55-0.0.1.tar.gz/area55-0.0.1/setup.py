from setuptools import setup, find_packages

setup(
    name="area55",
    version="0.0.1",
    author="priyanshu",
    author_email="iampriyanshu55@gmail.com",
    description="Library for calculating area of shapes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
