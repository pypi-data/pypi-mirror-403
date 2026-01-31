from setuptools import setup, find_packages

setup(
    name="snras", 
    version="1.0.0",
    author="Ahmed Sattar Jabbar",
    author_email="me4022002@uomustansiriyah.edu.iq",
    description="A robust metric for exoplanet transit vetting in heteroscedastic light curves",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AhmedSattar/snras", # Replace with your actual GitHub link later
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Intended Audience :: Science/Research",
    ],
    python_requires='>=3.7',
    install_requires=[
        "numpy>=1.18.0",
        "matplotlib>=3.1.0",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/AhmedSattar/snras/issues",
        "Documentation": "https://github.com/AhmedSattar/snras/wiki",
        "Source Code": "https://github.com/AhmedSattar/snras",
        "Research Reference": "https://doi.org/10.1051/0004-6361/202659231", # Placeholder for your A&A DOI
    },
)