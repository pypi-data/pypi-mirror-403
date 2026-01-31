from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")



setup(
    name= 'WPP-tools',
    version= '0.3.6',
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="William Olson",
    author_email="Blueshadow0324@gmail.com",
    packages=find_packages(),
    install_requires=[
        "streamlit"
    ]
)