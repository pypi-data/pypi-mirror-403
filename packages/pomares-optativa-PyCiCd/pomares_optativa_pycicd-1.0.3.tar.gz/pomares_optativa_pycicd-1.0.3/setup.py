from setuptools import setup, find_packages


setup(
    name="pomares_optativa_PyCiCd",
    version="1.0.3",
    author="Javier Pomares Gomez",
    author_email="javierpomaresgomez@gmail.com",
    description="Proyecto de practica",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
    ],
)
