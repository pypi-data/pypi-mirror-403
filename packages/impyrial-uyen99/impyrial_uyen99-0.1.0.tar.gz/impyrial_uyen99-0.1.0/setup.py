# Import required functions
from setuptools import setup, find_packages

# Call setup function
setup(
    author="uyenhoang99",
    description="A package for converting impyiral lengths and weights.",
    name="impyrial_uyen99",
    packages=find_packages(include=["impyrial", "impyrial.*"]),
    version="0.1.0",
    install_requires = ['pandas', 'scipy', 'matplotlib']
)