from setuptools import setup, find_packages

setup(
    name="cipfsuf",
    version="1.0.0",
    author="MurilooPrDev",
    description="The IPFS Unfuccker - Global CID Propagation Tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MurilooPrDev/CIPFSUF",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "cipfsuf=scripts.gatekeeper:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
