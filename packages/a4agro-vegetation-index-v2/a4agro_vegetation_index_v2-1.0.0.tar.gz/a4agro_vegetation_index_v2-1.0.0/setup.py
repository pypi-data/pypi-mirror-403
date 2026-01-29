from setuptools import setup, find_packages

VERSION = "1.0.0"
DESCRIPTION = "This is a package for a4agro vegetation index calculation and generation of figures"
LONG_DESCRIPTION = "Package would be created to calculate vegetation index and generate figures getting example arcgisPro plataform, this package actualy only support planet imagery 8bands"

setup(
    name="a4agro_vegetation_index_v2",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author="a4agrodevops",
    author_email="devops.a4agro@gmail.com",
    packages=find_packages(),
    keywords=["vegetation", "index", "a4agro"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=[
        "numpy",
        "matplotlib",
        "rasterio",
        "scipy",
        "PyQt6",
        "scikit-image",
    ],
)
