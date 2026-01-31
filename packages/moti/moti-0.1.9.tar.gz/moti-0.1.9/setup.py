from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="moti",
    version="0.1.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automatically runs run.py in background on install",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaydeepgajera/moti",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "seleniumbase",
    ],
)
