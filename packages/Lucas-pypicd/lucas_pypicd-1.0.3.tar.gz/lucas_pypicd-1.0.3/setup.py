from setuptools import setup, find_packages


setup(
    name="Lucas_pypicd",
    version="1.0.3",
    author="Kluklas",
    author_email="kluklassmr@gmail.com",
    description="GitHub_Actions with Roman",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "flake8",
    ],
)