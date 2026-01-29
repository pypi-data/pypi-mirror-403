from setuptools import setup, find_packages


setup(
    name="istar_pycicd",
    version="1.0.4",
    author="Istar Hernández",
    author_email="istarhf110809@gmail.com",
    description="Descripción de tu proyecto",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
    ],
)