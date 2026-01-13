from setuptools import setup, find_packages

setup(
    name="bitart",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "Pillow",
        "PyYAML",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "bitart=bitart.cli:main",
        ],
    },
    author="Vibecoder",
    description="A procedural integer art generator (Python port)",
    license="AGPLv3",
)
