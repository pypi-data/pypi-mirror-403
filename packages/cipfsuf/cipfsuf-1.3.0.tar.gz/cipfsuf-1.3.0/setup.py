from setuptools import setup, find_packages

setup(
    name="cipfsuf",
    version="1.3.0",
    author="MurilooPrDev",
    packages=find_packages(),
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "cipfsuf=cipfsuf:main",
        ],
    },
)
