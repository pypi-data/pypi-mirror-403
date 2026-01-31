from setuptools import setup

setup(
    name="cipfsuf",
    version="1.1.0",
    author="MurilooPrDev",
    py_modules=["gatekeeper"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "cipfsuf=gatekeeper:main",
        ],
    },
)
