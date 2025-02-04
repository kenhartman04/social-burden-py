from setuptools import setup, find_packages

setup(
    name="social_burden_tool",
    version="0.1.0",
    description="A Python package for calculating Social Burden Metrics.",
    author="Kendall Hartman",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "geopandas",
        "scipy",
        "logging",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
