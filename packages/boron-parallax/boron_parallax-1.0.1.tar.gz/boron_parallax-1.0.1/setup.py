from setuptools import setup, find_packages

setup(
    name="boron-parallax",
    version="1.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "lark",  # Automatically installs dependencies
    ],
    package_data={
        # This includes non-python files (like your grammar)
        "parallax_core": ["grammar.lark"], 
    },
    entry_points={
        "console_scripts": [
            # THIS IS THE MAGIC LINE
            # It maps the command "prlx" to the function "entry_point" in main.py
            "prlx=parallax_core.main:entry_point", 
        ],
    },
)