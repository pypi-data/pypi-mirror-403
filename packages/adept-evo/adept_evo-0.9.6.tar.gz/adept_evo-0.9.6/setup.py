from setuptools import setup, find_packages

setup(
    name="adept-evo",
    version="0.9.6",
    author="Taner Karagol",
    author_email="taner.karagol@gmail.com",
    description="Automated Dynamics-Aware Evolutionary Profiling Tool (ADEPT)",
    long_description=open("README.md").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/karagol-taner/Dynamics-aware-Evolutionary-Profiling",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
    ],
    entry_points={
        "console_scripts": [
            "adept=adept.cli:main",  # This creates the 'adept' command
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires='>=3.7',
)
