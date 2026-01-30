from setuptools import setup, find_packages
from pathlib import Path

# This part is what sends your README content to the website
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="boron-parallax",
    version="1.0.4",
    description="The World's First Timeline-Oriented Programming Language",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "lark",
    ],
    package_data={
        "parallax_core": ["grammar.lark"],
    },
    entry_points={
        "console_scripts": [
            "prlx=parallax_core.main:entry_point",
        ],
    },
    author="Harsith",
    url="https://github.com/harsith/parallax",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.10',
)