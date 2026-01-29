from setuptools import setup, find_packages

setup(
    name="diego-ci-cd",
    version="1.0.4",
    author="Diego Garcia",
    author_email="correoinformatica777@gmail.com",
    description="Descripción de tu proyecto",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
        "setuptools"
    ],
)
