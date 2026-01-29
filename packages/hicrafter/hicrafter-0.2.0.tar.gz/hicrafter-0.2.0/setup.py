from setuptools import setup, find_packages

setup(
    name="hicrafter",
    version="0.2.0",
    description="HI Intensity Mapping generator with LHS sampling & multi-CPU batching",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21",
        "healpy>=1.15",
        "camb>=0.5",
        "glass>=0.5", 
        "scipy>=1.8",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    python_requires=">=3.9",
)
