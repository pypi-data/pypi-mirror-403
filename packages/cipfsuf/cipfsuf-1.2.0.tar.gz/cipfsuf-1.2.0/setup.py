from setuptools import setup

setup(
    name="cipfsuf",
    version="1.2.0",
    author="MurilooPrDev",
    py_modules=["cipfsuf"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "cipfsuf=cipfsuf:main",
        ],
    },
)
