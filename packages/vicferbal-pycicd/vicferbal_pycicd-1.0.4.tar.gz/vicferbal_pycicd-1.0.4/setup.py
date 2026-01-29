from setuptools import setup, find_packages

setup(
    name="vicferbal_pycicd",
    version="1.0.4",
    author="Víctor Manuel Ferrández Ballester",
    author_email="vicferbal@alu.edu.gva.es",
    description="Descripción ",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
    ],
)