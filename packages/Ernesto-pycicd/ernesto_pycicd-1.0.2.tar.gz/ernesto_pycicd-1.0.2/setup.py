from setuptools import setup, find_packages


setup(
    name="Ernesto_pycicd",
    version="1.0.2",
    author="Ernesto Ruiz Hortelano",
    author_email="coperinfofp@gmail.com",
    description="Descripción de tu proyecto",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
    ],
)
