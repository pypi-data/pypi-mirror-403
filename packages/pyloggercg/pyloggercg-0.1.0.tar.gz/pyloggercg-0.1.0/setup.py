from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyloggercg",
    version="0.1.0",
    packages=find_packages(),
    author="CoolGuy158-Git",
    license="MIT",
    python_requires='>=3.7',
    keywords="Terminal Logger Simple Syntax For Python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
