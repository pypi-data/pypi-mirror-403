from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ez-autoprep",
    version="0.1.0",
    author="Hassan Rasheed",
    author_email="craftycode121@gmail.com",
    description="A library for automated data preprocessing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hassanrasheed-pydev/AutoPrep",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "numpy>=2.4.1",
    ],
    keywords="preprocessing, data-science, machine-learning, transformers",
)